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
  A[/Homebuyer Income Limit/]
  B[/Renter Income Limit/]
  A --> C["Multiply by 3.5 \n (or desired home price to income ratio)"]
  B --> D["Divide by 12\n (months in a year)"]
  D --> E["Multiply by 0.3\n (30% of monthly income)"]
  C ---> F[\Max Affordable For-Sale Price\]
  E --> G[\Max Affordable Rent\]