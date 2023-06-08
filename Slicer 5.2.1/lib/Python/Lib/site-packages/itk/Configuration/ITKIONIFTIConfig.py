depends = ('ITKPyBase', 'ITKTransform', 'ITKIOImageBase', )
templates = (  ('NiftiImageIOEnums', 'itk::NiftiImageIOEnums', 'itkNiftiImageIOEnums', False),
  ('NiftiImageIO', 'itk::NiftiImageIO', 'itkNiftiImageIO', True),
  ('NiftiImageIOFactory', 'itk::NiftiImageIOFactory', 'itkNiftiImageIOFactory', True),
)
factories = (("ImageIO","Nifti"),)
