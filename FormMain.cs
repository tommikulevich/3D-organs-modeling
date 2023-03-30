using SharpGL;
using SharpGL.Shaders;
using Assimp;
using System.Numerics;

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

        // Shader
        private ShaderProgram shaderProgram;

        // VBO and VAO
        private uint[] vertexBufferObject;

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

                    // Generate VBO and VAO
                   // InitializeVertexBufferObjects();
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

            // Initialize shader
            InitializeShader(gl);
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

            // Use the shader program
            if (shaderProgram != null)
            {
                shaderProgram.Bind(gl);
            }

            // Render the object
            if (model != null)
            {
                // Bind the VAO
                gl.BindBuffer(OpenGL.GL_ARRAY_BUFFER, vertexBufferObject[0]);

                // Iterate through all meshes in the model
                for (int i = 0; i < model.Meshes.Count; i++)
                {
                    var mesh = model.Meshes[i];
                    var material = model.Materials[mesh.MaterialIndex];

                    // Set the color and other material properties if available
                    if (material != null)
                    {
                        if (material.HasColorDiffuse)
                        {
                            var color = material.ColorDiffuse;
                            if (shaderProgram != null)
                            {
                                shaderProgram.SetUniform3(gl, "materialColor", color.R, color.G, color.B);
                            }
                        }
                    }

                    // Draw the mesh
                    int vertexOffset = mesh.VertexCount * i;
                    gl.DrawArrays(OpenGL.GL_TRIANGLES, vertexOffset, mesh.VertexCount);
                }

                // Unbind the VAO
                gl.BindBuffer(OpenGL.GL_ARRAY_BUFFER, 0);

                // Unbind the shader program
                if (shaderProgram != null)
                {
                    shaderProgram.Unbind(gl);
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

        private void InitializeVertexBufferObjects()
        {
            if (model == null) // Dodaj tę linię
            {
                return; // Dodaj tę linię
            }

            OpenGL gl = openGLControl.OpenGL;

            vertexBufferObject = new uint[model.Meshes.Count];
            gl.GenBuffers(model.Meshes.Count, vertexBufferObject);

            for (int i = 0; i < model.Meshes.Count; i++)
            {
                var mesh = model.Meshes[i];

                // Bind the VBO
                gl.BindBuffer(OpenGL.GL_ARRAY_BUFFER, vertexBufferObject[i]);

                // Set vertex buffer data
                float[] vertices = new float[mesh.VertexCount * 3];
                for (int j = 0; j < mesh.VertexCount; j++)
                {
                    vertices[j * 3 + 0] = mesh.Vertices[j].X;
                    vertices[j * 3 + 1] = mesh.Vertices[j].Y;
                    vertices[j * 3 + 2] = mesh.Vertices[j].Z;
                }
                gl.BufferData(OpenGL.GL_ARRAY_BUFFER, vertices, OpenGL.GL_STATIC_DRAW);

                // Set vertex attribute pointers
                uint positionAttributeLocation = (uint)shaderProgram.GetAttributeLocation(gl, "position");
                gl.EnableVertexAttribArray(positionAttributeLocation);
                gl.VertexAttribPointer(positionAttributeLocation, 3, OpenGL.GL_FLOAT, false, 0, IntPtr.Zero);

                // Unbind the VAO and VBO
               gl.BindBuffer(OpenGL.GL_ARRAY_BUFFER, 0);
            }
        }

        private void InitializeShader(OpenGL gl)
        {
            // Shader source code
            string vertexShaderSource = @"
        #version 330 core
        layout (location = 0) in vec3 position;

        uniform mat4 modelViewProjectionMatrix;

        void main()
        {
            gl_Position = modelViewProjectionMatrix * vec4(position, 1.0);
        }";

            string fragmentShaderSource = @"
        #version 330 core
        out vec4 fragColor;

        uniform vec3 materialColor;

        void main()
        {
            fragColor = vec4(materialColor, 1.0);
        }";

            // Compile and link shader program
            shaderProgram = new ShaderProgram();
            shaderProgram.Create(gl, vertexShaderSource, fragmentShaderSource, null);
            shaderProgram.AssertValid(gl);
        }


    }


}
