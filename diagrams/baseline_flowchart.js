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
  A{Is the Housing Unit\n For-Rent, or For-Sale}
  A -- For-Rent ---> B
  B{Is the Rent At or Below the\n Max Affordable Rent?}
  A -- For-Sale ---> C
  C{Is the Price At or Below the\n Max Affordable Price}
  B -- Yes ---> D
  C -- Yes ---> D
  D{Could the Unit\n be Unit Available?}
  D -- Yes ---> F
  F[The Unit is Included in the\n Baseline Amount of Affordable Housing]
mm  