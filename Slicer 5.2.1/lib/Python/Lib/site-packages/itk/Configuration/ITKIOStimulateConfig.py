depends = ('ITKPyBase', 'ITKIOImageBase', )
templates = (  ('StimulateImageIO', 'itk::StimulateImageIO', 'itkStimulateImageIO', True),
  ('StimulateImageIOFactory', 'itk::StimulateImageIOFactory', 'itkStimulateImageIOFactory', True),
)
factories = (("ImageIO","Stimulate"),)
