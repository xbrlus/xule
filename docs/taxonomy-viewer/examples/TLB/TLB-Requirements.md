# TLB Requirements.

- Define a two dimensional layout for tabular data presentation, with an additional dimension representing the properties associated with each grid
- Each cell in the grid should represent the value of a fact based on its dimensional coordinates
- The layout format should provide a efficient way to define all the dimensional aspects of every cell in the grid, including:
  - The dimensions and their members that define the coordinates of each cell
- The layout should allow the ability to use existing networks to define dimension and member combinations without specifiying each combination explicitly in the layout
- The layout designed should be able to deine the dimensions and members  associated with each specific row and the dimensions and members associated with each specific column, as well as the dimensions and members that are common to all cells in the grid. The intersection of these three sets of dimensions and members should define the coordinates of each cell in the grid, allowing for a more efficient representation of the dimensionality of the data.
- The layout should support the ability to provide labels associated with each row and column, that an be expressed in multoiple languages and with different label types, to allow for more flexible presentation of the data in the grid.
- The layout should be able to support the ability to define the location of total values for dimensions that are included in the layout, to allow for more flexible presentation of aggregated data in the grid.
- If a network is used to identify the members of a dimension for a row or column there must be a way to specify additional dimensions and members that are not included in the network but are still relevant to the cells in that row or column, to allow for more flexible representation of the dimensionality of the data in the grid.
- The labels should support the ability to nest the labels for rows and columns to allow for hierarchical representation of the data in the grid.
- The layout should support the ability to define multiple layouts within a single model to allow for different presentations of the same data in the grid.
- The layout should support adding labels that are specific to a column or row that can be used for coordinate labeling without affecting the labels of the dimensions and members that define the coordinates of the cells in the grid. 
- Coordinate labels should be able to be defines explicitly as part oflayout or derived as a series with specific intervals and prefix or suffix if necessary such as R010 or C001 for rows and columns respectively.
- The layout model should be able to be based on a cube so that the facts thata re valid in the cube will be the only facts that appear in the layout, and values that are not covered by the cube but exist as a cell in the layout model should be grayed out to indicate that they are not valid facts in the cube.
- The layout model should support typed dimensions or open dimensions that support labels and do not have to define every typed member as these are not known when the layout is defined.