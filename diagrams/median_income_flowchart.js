%%{
    init: {
      'theme': 'base',
      'themeVariables': {
        'primaryColor': '#245d38',
        'primaryTextColor': '#fff',
        'primaryBorderColor': '#ffd100',
        'lineColor': '#001970',
        'secondaryColor': '#5c666f',
        'tertiaryColor': '#ffd100'
      }
    }
  }%%
  
  graph LR
  accTitle: test
  accDescr: test
  A{Choose a Year}
  A --> B{Choose an Income\n Limit Type}
  B --> C[/Own Area\n Median Income/]
  B --> D[/Neighboring County's\n Area Median Income/]
  B --> E[/State Household\n Median Income/]
  C --> F{Choose a\n Household Size}
  D --> F{Choose a\n Household Size}
  F --> G[/From\n 1 to 8/]
  F --> H[/Family/]
  E --> I[\Selected Median Income\]
  G --> I[\Selected Median Income\]
  H --> I[\Selected Median Income\]