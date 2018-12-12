library(shinydashboard)
library(leaflet)
library(dplyr)
library(curl) 
library(RProtoBuf) 
library(jsonlite)
library(data.table)

# 1=South, 2=East, 3=West, 4=North
dirColors <-c("1"="#595490", "2"="#527525", "3"="#A93F35", "4"="#BA48AA")

getMetroData <- function() {
  TVechiclesURL3 <- "https://api-v3.mbta.com/vehicles"
  vehicles<-data.frame(fromJSON(paste(TVechiclesURL3), flatten = TRUE)$data)
  names(vehicles) <- c("vehicle_id",
                       "type",
                      "bearing",
                      "curr_status",
                      "curr_stop_sequence",
                      "direction_id",
                      "label",
                      "latitude",
                      "longitude",
                      "speed",
                      "system_time",
                      "self",
                      "route_id",
                      "rtype",
                      "stop_id",
                      "stype",
                      "trip_id",
                      "ttype"
                       )
  drops <- c("type",
             "bearing",
             "label",
             "speed",
             "self",
             "stype",
             "rtype",
             "ttype")
  
  routes <- c("Green-B", "Green-C", "Green-D", "Green-E", "Red", "Orange", "Blue")
  vehicles <- vehicles[vehicles$route_id %in% routes,]
  vehicles <- vehicles[ , !(names(vehicles) %in% drops)]
  #vehicles$direction_id[vehicles$direction_id == 0 & vehicles$route_id %in% c("Red","Blue", "Orange")] <- 2
  #vehicles$direction_id[vehicles$direction_id == 1 & vehicles$route_id %in% c("Red","Blue", "Orange")] <- 3
  vehicles

}

getMetroStopsData <- function() {
  TStopsURL3 <- "https://api-v3.mbta.com/stops"
  StopsComplete<-data.frame(fromJSON(paste(TStopsURL3))$data)
  StopsComplete<-subset(StopsComplete, is.na(StopsComplete$relationships$parent_station$data$id) == FALSE)
  StopsComplete<-StopsComplete[StopsComplete$id > 70000 & StopsComplete$id <75000,]
  StopsComplete<-StopsComplete[!duplicated(StopsComplete$relationships$parent_station$data$id,
                                           StopsComplete$attributes$latitude,
                                           StopsComplete$attributes$longitude),]
  StopsComplete
}

# Load static trip and shape data
trips  <- read.csv("../datasets.nosync/MBTA_GTFS/trips.txt", header = TRUE, stringsAsFactors = FALSE)
#trips  <- readRDS("metrotransit-data/rds/trips.rds")
shapes  <- read.csv("../datasets.nosync/MBTA_GTFS/shapes.txt", header = TRUE, stringsAsFactors = FALSE)
#shapes <- readRDS("metrotransit-data/rds/shapes.rds")


# Get the shape for a particular route. This isn't perfect. Each route has a
# large number of different trips, and each trip can have a different shape.
# This function simply returns the most commonly-used shape across all trips for
# a particular route.
get_route_shape <- function(route) {
  routeid <- paste0(route)
  # For this route, get all the shape_ids listed in trips, and a count of how
  # many times each shape is used. We'll just pick the most commonly-used shape.
  shape_counts <- trips %>%
    filter(route_id == routeid) %>%
    group_by(shape_id) %>%
    summarise(n = n()) %>%
    arrange(-n)
  if(route=="Red"){
    shapeid <- shape_counts$shape_id[c(1)]
    shapeid<-as.character(shapeid)
    shapes %>% filter(shape_id == shapeid)
  }
  else{
    shapeid <- shape_counts$shape_id[1]
    shapeid<-as.character(shapeid)
    # Get the coordinates for the shape_id
    shapes %>% filter(shape_id == shapeid)
  }
}


function(input, output, session) {

  # Route select input box
  output$routeSelect <- renderUI({
    #live_vehicles <- getMetroData("VehicleLocations/0")
    live_vehicles <- getMetroData()

    routeNums <- c("All", "Green-B", "Green-C", "Green-D", "Green-E", "Red", "Orange", "Blue")
    # Add names, so that we can add all=0
    
    selectInput("routeNum", "Route", choices = routeNums, selected = "All")
  })
  
  searchResult<- reactive({
    stops_data  <- read.csv("../datasets.nosync/stop_sequence.csv", header = TRUE, stringsAsFactors = FALSE)
    if (input$routeNum == "All"){
      stops=sort(stops_data$stop_name)
      return(stops)
    } else {
      stops=sort(stops_data[stops_data$route_id == input$routeNum,]$stop_name)
      return(stops)
    }
  })
  
  output$selectUI <- renderUI({ 
    selectInput("stopName", "Select your stop", searchResult() )
  })

  # Locations of all active vehicles
  vehicleLocations <- reactive({
    input$refresh # Refresh if button clicked

    # Get interval (minimum 30)
    interval <- max(as.numeric(input$interval), 30)
    # Invalidate this reactive after the interval has passed, so that data is
    # fetched again.
    invalidateLater(interval * 1000, session)

    getMetroData()
  })

  # Locations of vehicles for a particular route
  routeVehicleLocations <- reactive({
    if (is.null(input$routeNum))
      return()

    locations <- vehicleLocations()
    if (input$routeNum == 'All')
      return(locations)
    
    locations[locations$route_id == input$routeNum, ]
  })
  
  predictionsByStop <- reactive({
    predictions  <- read.csv("../dashboard/prediction.csv", header = TRUE, stringsAsFactors = FALSE)
    
    if(is.null(input$stopName)){
      return(predictions)
    }
    else{
      return(predictions[predictions$stop_name == input$stopName,])
    }
  })

  # Get time that vehicles locations were updated
  lastUpdateTime <- reactive({
    vehicleLocations() # Trigger this reactive when vehicles locations are updated
    Sys.time()
  })

  # Number of seconds since last update
  output$timeSinceLastUpdate <- renderUI({
    # Trigger this every 5 seconds
    invalidateLater(5000, session)
    p(
      class = "text-muted",
      "Data refreshed ",
      round(difftime(Sys.time(), lastUpdateTime(), units="secs")),
      " seconds ago."
    )
  })

  output$numVehiclesTable <- renderUI({
    locations <- routeVehicleLocations()
    
    #print(nrow(locations), length(locations))
    if (length(locations) == 0 || nrow(locations) == 0)
      return(NULL)

    # Create a Bootstrap-styled table
    tags$table(class = "table",
      tags$thead(tags$tr(
        tags$th("Direction"),
        tags$th("Number of vehicles")
      )),
      tags$tbody(
        tags$tr(
          tags$td("Inbound"),
          tags$td(nrow(locations[locations$direction_id == "1",]))
        ),
        tags$tr(
          tags$td("Outbound"),
          tags$td(nrow(locations[locations$direction_id == "0",]))
        ),
        tags$tr(class = "active",
          tags$td("Total"),
          tags$td(nrow(locations))
        )
      )
    )
  })
  
  output$prediction <- renderUI({
    
    locations <- routeVehicleLocations()
    predictions <- predictionsByStop()
    
    
    #print(nrow(locations), length(locations))
    
    if (length(locations) == 0 || nrow(locations) == 0)
      return(NULL)
    
    predictions['ols'] <- abs(predictions['ols'])
    
    inbound_ols<-paste(floor(min(subset(predictions, direction_id==1)$ols)/60), " mins away")
    outbound_ols<-paste(floor(min(subset(predictions, direction_id==0)$ols)/60), " mins away")
    inbound_dnn<-paste(floor(min(subset(predictions, direction_id==1)$dnn)/60), " mins away")
    outbound_dnn<-paste(floor(min(subset(predictions, direction_id==0)$dnn)/60), " mins away")
    inbound_xgb<-paste(floor(min(subset(predictions, direction_id==1)$xgb)/60), " mins away")
    outbound_xgb<-paste(floor(min(subset(predictions, direction_id==0)$xgb)/60), " mins away")
    
    predictions['mav']<-(predictions['distance']/predictions['velocity'])*60*60
    
    inbound_mav<-paste(floor(min(subset(predictions, direction_id==1)$mav)/60), " mins away")
    outbound_mav<-paste(floor(min(subset(predictions, direction_id==0)$mav)/60), " mins away")
    
    predictions['mavxgb'] <- with(predictions, ifelse(distance<1, predictions['xgb'], 0.75*predictions['mav']+0.25*predictions['xgb']))
    
    inbound_mavxgb<-paste(floor(min(subset(predictions, direction_id==1)$mavxgb)/60), " mins away")
    outbound_mavxgb<-paste(floor(min(subset(predictions, direction_id==0)$mavxgb)/60), " mins away")
    View(predictions)
    
    # Create a Bootstrap-styled table
    tags$table(class = "table",
               tags$thead(tags$tr(
                 tags$th("Model"),
                 tags$th("Inbound Arrivals"),
                 tags$th("Outbound Arrivals")
               )),
               tags$tbody(
                 tags$tr(
                  tags$td("XGB"),
                  tags$td(inbound_xgb),
                  tags$td(outbound_xgb)
                 ),
                 tags$tr(
                   tags$td("OLS"),
                   tags$td(inbound_ols),
                   tags$td(outbound_ols)
                 ),
                 tags$tr(
                   tags$td("DNN"),
                   tags$td(inbound_dnn),
                   tags$td(outbound_dnn)
                 ),
                 tags$tr(
                   tags$td("MAV+XGB"),
                   tags$td(inbound_mavxgb),
                   tags$td(outbound_mavxgb)
                 )
               )
    )
  })

  # Store last zoom button value so we can detect when it's clicked
  lastZoomButtonValue <- NULL

  output$map <- renderLeaflet({
    locations <- routeVehicleLocations()
    #View(locations)
    if (length(locations) == 0) {
      map <- setView(lng = 42.3601, lat = -71.0589, zoom = 13) %>% 
        addProviderTiles("CartoDB.Positron") 
      rezoom <- "first"
      # If zoom button was clicked this time, and store the value, and rezoom
      if (!identical(lastZoomButtonValue, input$zoomButton)) {
        lastZoomButtonValue <<- input$zoomButton
        rezoom <- "always"
      }
      
      map <- map %>% mapOptions(zoomToLimits = rezoom)
      
      map
    } else {
      #Show only selected directions
      locations <- filter(locations, direction_id %in% as.numeric(input$directions))
      getMarkerColor1 <- function(locations) {
        sapply(locations$route_id, function(mag) {
          if(mag %in% c("Green-B","Green-C","Green-D","Green-E")) {
            "green"
          } else if(mag == "Orange") {
            "orange"
          } else if(mag == "Blue") {
            "blue"
          } else if(mag == "Red") {
            "red"
          } })
      }
      
      getMarkerColor2 <- function(locations) {
        sapply(locations$direction_id, function(mag) {
          if(mag %in% c(0,2)) {
            "light"
          } else {
            "dark"
          } })
      }
      
      getColorLines <- function(routec) {
        if(length(routec)>1)
          routec<-routec[1]
        if(routec %in% c("Green-B","Green-C","Green-D","Green-E")) {
          "green"
        } else if(routec == "Orange") {
          "orange"
        } else if(routec == "Blue") {
          "blue"
        } else if(routec == "Red") {
          "red"
        } 
      }
      icons <- awesomeIcons(
        icon = 'fa-subway',
        iconColor = "black",
        library = 'fa',
        markerColor = gsub("lightorange", "orange", paste0(getMarkerColor2(locations),unname(getMarkerColor1(locations))))
      )
      
      tIcon <- makeIcon(
        iconUrl = "MBTA.png",
        iconWidth = 10, 
        iconHeight = 10
      )
      
      StopsComplete<-getMetroStopsData()
      StopsComplete$attributes$name<-as.character(StopsComplete$attributes$name)
      StopsComplete$attributes$name<-gsub("Outbound","",StopsComplete$attributes$name)
      StopsComplete$attributes$name<-gsub("Inbound","",StopsComplete$attributes$name)
      StopsComplete$attributes$name<-gsub("-","",StopsComplete$attributes$name)
      
      
      # possible directions for train routes
      dirPal <- colorFactor(dirColors, names(dirColors))
      map <- leaflet(locations) %>%
        setView(lng = mean(as.numeric(locations$longitude)), 
                lat = mean(as.numeric(locations$latitude)), zoom = 13) %>% 
        addProviderTiles("CartoDB.Positron") %>%
        addAwesomeMarkers(
          ~longitude,
          ~latitude,
          #icon = icons,
          icon = icons,
          label = ~as.character(vehicle_id)
        )%>%
        addMarkers(
          as.numeric(StopsComplete$attributes$longitude),
          as.numeric(StopsComplete$attributes$latitude),
          icon=tIcon,
          label = as.character(StopsComplete$attributes$name)
        ) 
      
      route_shape <- get_route_shape(input$routeNum)
      
      if (input$routeNum != "All") {
        route_shape <- get_route_shape(input$routeNum)
        map <- addPolylines(map,
                            route_shape$shape_pt_lon,
                            route_shape$shape_pt_lat,
                            color = getColorLines(input$routeNum),
                            opacity = 0.5,
                            fill = FALSE
        )
      }
      else{
        routeNums <- c("All", "Green-B", "Green-C", "Green-D", "Green-E", "Red", "Orange", "Blue")
        for(i in routeNums[c(2:length(routeNums))]){
          route_shape <- get_route_shape(i)
          map <- addPolylines(map,
                              route_shape$shape_pt_lon,
                              route_shape$shape_pt_lat,
                              color = getColorLines(i),
                              opacity = 0.5,
                              fill = FALSE
          )
        }
      }
      
      rezoom <- "first"
      # If zoom button was clicked this time, and store the value, and rezoom
      if (!identical(lastZoomButtonValue, input$zoomButton)) {
        lastZoomButtonValue <<- input$zoomButton
        rezoom <- "always"
      }
      
      map <- map %>% mapOptions(zoomToLimits = rezoom)
      
      map
      
    }
    
  })
}
