library(shinydashboard)
library(leaflet)

header <- dashboardHeader(
  title = "Boston - XGBoost powered Arrival time prediction"
)

body <- dashboardBody(
  fluidRow(
    column(width = 9,
      box(width = NULL, solidHeader = TRUE,
        leafletOutput("map", height = 500)
      ),
      box(width = NULL,
          uiOutput("prediction")
      )
    ),
    column(width = 3,
      box(width = NULL, status = "warning",
        uiOutput("routeSelect"),
        htmlOutput("selectUI"),
        checkboxGroupInput("directions", "Show",
          choices = c(
            Inbound = 1,
            Outbound = 0
          ),
          selected = c(0, 1)
        ),
        p(
          class = "text-muted",
          paste("Note: Filter based on Inbound and Outbound trains."
          )
        ),
        actionButton("zoomButton", "Zoom to fit trains")
      ),
      box(width = NULL, status = "warning",
        selectInput("interval", "Refresh interval",
          choices = c(
            "30 seconds" = 30,
            "1 minute" = 60,
            "2 minutes" = 120,
            "5 minutes" = 300,
            "10 minutes" = 600
          ),
          selected = "60"
        ),
        uiOutput("timeSinceLastUpdate"),
        actionButton("refresh", "Refresh now"),
        p(class = "text-muted",
          br(),
          "Source data updates every 30 seconds."
        )
      ),
      box(width = NULL,
          uiOutput("numVehiclesTable")
      )
    )
  )
)

dashboardPage(
  header,
  dashboardSidebar(disable = TRUE),
  body
)
