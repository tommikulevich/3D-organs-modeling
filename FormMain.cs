using SharpGL;
using Assimp;


namespace MSN_GUI
{
    public partial class FormMSN : Form
    {
        // Graphics parametres
        private OpenGLControl openGLControl => openGLControlMain;
        private Scene model;

        // Object parametres
        private Vector3D objectCenter;
        private Vector3D objectSize;

        // Rotating parametres
        private float rotationX, rotationY;
        private Point lastMousePosition;
        private float cameraDist;
        private float zoom;

        public FormMSN()
        {
            InitializeComponent();
        }

        // Choosing .obj file
        private void chooseObjToolStripMenuItem_Click(object sender, EventArgs e)
        {
            using (OpenFileDialog openFileDialog = new OpenFileDialog())
            {
                openFileDialog.Filter = "OBJ Files (*.obj)|*.obj";

                if (openFileDialog.ShowDialog() == DialogResult.OK)
                {
                    string filePath = openFileDialog.FileName;
                    AssimpContext importer = new AssimpContext();
                    model = importer.ImportFile(filePath, PostProcessPreset.TargetRealTimeMaximumQuality);

                    // Calculate bounding box, center and size of the object
                    calculateBoundingBox(model, out Vector3D min, out Vector3D max, out Vector3D size);
                    objectCenter = (max + min) / 2;
                    objectSize = size;
                }
            }
        }

        // Help section
        private void helpToolStripMenuItem_Click(object sender, EventArgs e)
        {
            string title = "Helpdesk";
            string message = "To see object, you need to click 'Select .obj file' and pick a file with .obj extension";
            MessageBox.Show(message, title, MessageBoxButtons.OK, MessageBoxIcon.Information);
        }

        // Calculating object bounding box to set object correctly on the screen
        private void calculateBoundingBox(Scene model, out Vector3D min, out Vector3D max, out Vector3D size)
        {
            min = new Vector3D(float.MaxValue, float.MaxValue, float.MaxValue);
            max = new Vector3D(float.MinValue, float.MinValue, float.MinValue);

            if (model != null)
            {
                foreach (var mesh in model.Meshes)
                {
                    foreach (var vertex in mesh.Vertices)
                    {
                        min.X = Math.Min(min.X, vertex.X);
                        min.Y = Math.Min(min.Y, vertex.Y);
                        min.Z = Math.Min(min.Z, vertex.Z);

                        max.X = Math.Max(max.X, vertex.X);
                        max.Y = Math.Max(max.Y, vertex.Y);
                        max.Z = Math.Max(max.Z, vertex.Z);
                    }
                }
            }

            size = max - min;
        }

        // Loading the form 
        private void FormMain_Load(object sender, EventArgs e)
        {
            openGLControl.OpenGLInitialized += openGLControlMain_OpenGLInitialized!;
            openGLControl.OpenGLDraw += openGLControlMain_OpenGLDraw!;

            openGLControl.MouseDown += openGLControlMain_MouseDown!;
            openGLControl.MouseMove += openGLControlMain_MouseMove!;
            openGLControl.MouseWheel += OpenGLControl_MouseWheel;
        }

        // Graphics initialization
        private void openGLControlMain_OpenGLInitialized(object sender, EventArgs e)
        {
            OpenGL gl = openGLControl.OpenGL;

            gl.LoadIdentity();
            gl.Perspective(45.0f, (double)openGLControl.Width / (double)openGLControl.Height, 1, 1000);
            gl.MatrixMode(OpenGL.GL_MODELVIEW);
            gl.Enable(OpenGL.GL_DEPTH_TEST);
             
            // Lighting
            gl.Enable(OpenGL.GL_LIGHTING);
            gl.Enable(OpenGL.GL_LIGHT0);
            gl.Enable(OpenGL.GL_COLOR_MATERIAL);

            gl.ShadeModel(OpenGL.GL_SMOOTH);
        }

        // Graphics drawing and refreshing
        private void openGLControlMain_OpenGLDraw(object sender, RenderEventArgs e)
        {
            OpenGL gl = openGLControl.OpenGL;
            float scaleFactor = 0.05f;

            gl.Clear(OpenGL.GL_COLOR_BUFFER_BIT | OpenGL.GL_DEPTH_BUFFER_BIT);
            gl.LoadIdentity();

            // Camera
            float sizeFactor = Math.Max(objectSize.X, Math.Max(objectSize.Y, objectSize.Z)) * scaleFactor;
            cameraDist = 2.5f * sizeFactor + zoom;
            gl.LookAt(0, 0, cameraDist, 0, 0, 0, 0, 1, 0);

            // Rotation
            gl.Rotate(rotationX, 1.0f, 0.0f, 0.0f);
            gl.Rotate(rotationY, 0.0f, 1.0f, 0.0f);
            
            // Scale and center the object
            gl.Scale(scaleFactor, scaleFactor, scaleFactor);
            gl.Translate(-objectCenter.X, -objectCenter.Y, -objectCenter.Z);
           
            if (model != null)
            {               
                for (int i = 0; i < model.Meshes.Count; i++)
                {
                    var mesh = model.Meshes[i];
                    var material = model.Materials[mesh.MaterialIndex];

                    if (material != null)
                    {
                        if (material.HasColorDiffuse)
                        {
                            var color = material.ColorDiffuse;
                            gl.Color(color.R, color.G, color.B, color.A);
                        }
                    }

                    gl.Begin(OpenGL.GL_TRIANGLES);
                    foreach (var face in mesh.Faces)
                    {
                        foreach (var index in face.Indices)
                        {
                            var vertex = mesh.Vertices[index];
                            gl.Vertex(vertex.X, vertex.Y, vertex.Z);
                            
                            if (mesh.HasNormals)
                            {
                                var normal = mesh.Normals[index];
                                gl.Normal(normal.X, normal.Y, normal.Z);
                            }

                            if (mesh.HasTextureCoords(0))
                            {
                                var texCoord = mesh.TextureCoordinateChannels[0][index];
                                gl.TexCoord(texCoord.X, texCoord.Y);
                            }
                        }
                    }
                    gl.End();
                }
            }

            gl.Flush();
        }

        // Mouse behaviour I
        private void openGLControlMain_MouseDown(object sender, MouseEventArgs e)
        {
            lastMousePosition = e.Location;
        }

        // Mouse behaviour II
        private void openGLControlMain_MouseMove(object sender, MouseEventArgs e)
        {
            if (e.Button == MouseButtons.Left)
            {
                float dx = e.X - lastMousePosition.X;
                float dy = e.Y - lastMousePosition.Y;

                rotationY += dx * 0.5f;
                rotationX += dy * 0.5f;

                openGLControl.Invalidate();
            }
            
            lastMousePosition = e.Location;
        }

        // Mouse scroll
        private void OpenGLControl_MouseWheel(object? sender, MouseEventArgs e)
        {
            if (e.Delta > 0)
            {
                // Move camera to object
                zoom -= 1.0f;
            }
            else
            {
                // Move camera from object
                zoom += 1.0f;
            }
            openGLControl.Invalidate();
        }

    }
}
