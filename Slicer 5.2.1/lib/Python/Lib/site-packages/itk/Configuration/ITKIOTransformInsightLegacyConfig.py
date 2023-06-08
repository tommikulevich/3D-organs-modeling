depends = ('ITKPyBase', 'ITKIOTransformBase', )
templates = (  ('TxtTransformIOTemplate', 'itk::TxtTransformIOTemplate', 'itkTxtTransformIOTemplateD', False, 'double'),
  ('TxtTransformIOTemplate', 'itk::TxtTransformIOTemplate', 'itkTxtTransformIOTemplateF', False, 'float'),
  ('TxtTransformIOFactory', 'itk::TxtTransformIOFactory', 'itkTxtTransformIOFactory', True),
)
factories = (("TransformIO","Txt"),)
