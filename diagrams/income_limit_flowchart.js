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
  A[/Selected Median Income/]
  A --> B[Multiply by 0.6]
  A ---> D[\Homebuyer Income Limit\]
  B --> E[\Renter Income Limit\]
  