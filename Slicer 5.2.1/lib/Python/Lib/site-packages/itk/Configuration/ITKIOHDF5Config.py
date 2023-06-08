depends = ('ITKPyBase', 'ITKIOImageBase', )
templates = (  ('HDF5ImageIO', 'itk::HDF5ImageIO', 'itkHDF5ImageIO', True),
  ('HDF5ImageIOFactory', 'itk::HDF5ImageIOFactory', 'itkHDF5ImageIOFactory', True),
)
factories = (("ImageIO","HDF5"),)
