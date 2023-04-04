using SharpGL;
using SharpGL.Shaders;
using Assimp;
using System;
using System.Drawing;
using System.Windows.Forms;
using System.Runtime.InteropServices;


namespace MSN_GUI
{
    public partial class FormMSN : Form
    {
        // Graphics parametres
        private OpenGLControl openGLControl => openGLControlMain;
        private Scene model;
        private float[] backgroundColor = { 1.0f, 1.0f, 1.0f };

        // Object parametres
        private Vector3D objectCenter;
        private Vector3D objectSize;

        // Rotating parametres
        private float rotationX, rotationY;
        private Point lastMousePosition;
        private float cameraDist;
        private float zoom;

        private uint[] vboIds;
        private uint[] vaoIds;

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
                    // Clean up the old VBOs and VAOs
                    CleanupVBOsAndVAOs();

                    string filePath = openFileDialog.FileName;
                    AssimpContext importer = new AssimpContext();
                    model = importer.ImportFile(filePath, PostProcessPreset.TargetRealTimeMaximumQuality);

                    // Calculate bounding box, center and size of the object
                    calculateBoundingBox(model, out Vector3D min, out Vector3D max, out Vector3D size);
                    objectCenter = (max + min) / 2;
                    objectSize = size;

                    // Initialize VBOs and VAOs
                    InitializeVBOsAndVAOs();
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
            this.FormClosing += FormMSN_FormClosing;

            openGLControl.OpenGLInitialized += openGLControlMain_OpenGLInitialized!;
            openGLControl.OpenGLDraw += openGLControlMain_OpenGLDraw!;

            openGLControl.MouseDown += openGLControlMain_MouseDown!;
            openGLControl.MouseMove += openGLControlMain_MouseMove!;
            openGLControl.MouseWheel += OpenGLControl_MouseWheel;
        }

        private void FormMSN_FormClosing(object sender, FormClosingEventArgs e)
        {
            CleanupVBOsAndVAOs();
        }

        // Graphics initialization
        private void openGLControlMain_OpenGLInitialized(object sender, EventArgs e)
        {
            OpenGL gl = openGLControl.OpenGL;

            gl.LoadIdentity();
            gl.Perspective(45.0f, (double)openGLControl.Width / (double)openGLControl.Height, 1, 1000);
            gl.MatrixMode(OpenGL.GL_MODELVIEW);
            gl.Enable(OpenGL.GL_DEPTH_TEST);

            // Lighting colors
            float[] lightAmbient = { 0.5f, 0.5f, 0.5f, 1.0f };
            float[] lightDiffuse = { 1.0f, 1.0f, 1.0f, 1.0f };
            float[] lightSpecular = { 1.0f, 1.0f, 1.0f, 1.0f };
            float[] lightPosition = { 0.0f, 0.0f, 10.0f, 1.0f };

            // Light properties
            gl.Light(OpenGL.GL_LIGHT0, OpenGL.GL_AMBIENT, lightAmbient);
            gl.Light(OpenGL.GL_LIGHT0, OpenGL.GL_DIFFUSE, lightDiffuse);
            gl.Light(OpenGL.GL_LIGHT0, OpenGL.GL_SPECULAR, lightSpecular);
            gl.Light(OpenGL.GL_LIGHT0, OpenGL.GL_POSITION, lightPosition);

            // Lighting
            gl.Enable(OpenGL.GL_LIGHTING);
            gl.Enable(OpenGL.GL_LIGHT0);
            gl.Enable(OpenGL.GL_COLOR_MATERIAL);

            gl.ShadeModel(OpenGL.GL_SMOOTH);
            gl.Enable(OpenGL.GL_NORMALIZE);
        }

        // Graphics drawing and refreshing
        private void openGLControlMain_OpenGLDraw(object sender, RenderEventArgs e)
        {
            OpenGL gl = openGLControl.OpenGL;
            float scaleFactor = 0.05f;

            gl.ClearColor(backgroundColor[0], backgroundColor[1], backgroundColor[2], 1.0f);
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
                float[] colorEmission = { 0.0f, 0.0f, 0.0f, 1.0f };
                float[] colorAmbient = { 0.2f, 0.2f, 0.2f, 1.0f };

                gl.Material(OpenGL.GL_FRONT_AND_BACK, OpenGL.GL_EMISSION, colorEmission);
                gl.Material(OpenGL.GL_FRONT_AND_BACK, OpenGL.GL_AMBIENT, colorAmbient);

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
                            gl.Color(color.R, color.G, color.B, color.A);
                        }
                        if (material.HasColorSpecular)
                        {
                            var color = material.ColorSpecular;
                            gl.Material(OpenGL.GL_FRONT_AND_BACK, OpenGL.GL_SPECULAR, new float[] { color.R, color.G, color.B, color.A });
                            gl.Material(OpenGL.GL_FRONT_AND_BACK, OpenGL.GL_SHININESS, material.Shininess);
                        }
                        else
                        {
                            gl.Material(OpenGL.GL_FRONT_AND_BACK, OpenGL.GL_SPECULAR, new float[] { 0, 0, 0, 1 });
                            gl.Material(OpenGL.GL_FRONT_AND_BACK, OpenGL.GL_SHININESS, 0);
                        }
                    }

                    gl.BindVertexArray(vaoIds[i]);
                    gl.DrawArrays(OpenGL.GL_TRIANGLES, 0, mesh.Vertices.Count);
                    gl.BindVertexArray(0);
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

        private IntPtr GetIntPtrFromVector3DList(List<Vector3D> list)
        {
            float[] data = new float[list.Count * 3];

            for (int i = 0; i < list.Count; i++)
            {
                data[i * 3] = list[i].X;
                data[i * 3 + 1] = list[i].Y;
                data[i * 3 + 2] = list[i].Z;
            }

            GCHandle handle = GCHandle.Alloc(data, GCHandleType.Pinned);
            IntPtr pointer = handle.AddrOfPinnedObject();
            handle.Free();

            return pointer;
        }

        private void InitializeVBOsAndVAOs()
        {
            OpenGL gl = openGLControl.OpenGL;
            vboIds = new uint[model.Meshes.Count * 3];
            vaoIds = new uint[model.Meshes.Count];

            gl.GenBuffers(vboIds.Length, vboIds);
            gl.GenVertexArrays(vaoIds.Length, vaoIds);

            for (int i = 0; i < model.Meshes.Count; i++)
            {
                var mesh = model.Meshes[i];

                // Vertices
                gl.BindVertexArray(vaoIds[i]);
                gl.BindBuffer(OpenGL.GL_ARRAY_BUFFER, vboIds[i * 3]);
                IntPtr verticesPtr = GetIntPtrFromVector3DList(mesh.Vertices);
                gl.BufferData(OpenGL.GL_ARRAY_BUFFER, mesh.Vertices.Count * Marshal.SizeOf(typeof(Vector3D)), verticesPtr, OpenGL.GL_STATIC_DRAW);
                gl.EnableVertexAttribArray(0);
                gl.VertexAttribPointer(0, 3, OpenGL.GL_FLOAT, false, 0, IntPtr.Zero);

                // Normals
                if (mesh.HasNormals)
                {
                    gl.BindBuffer(OpenGL.GL_ARRAY_BUFFER, vboIds[i * 3 + 1]);
                    IntPtr normalsPtr = GetIntPtrFromVector3DList(mesh.Normals);
                    gl.BufferData(OpenGL.GL_ARRAY_BUFFER, mesh.Normals.Count * Marshal.SizeOf(typeof(Vector3D)), normalsPtr, OpenGL.GL_STATIC_DRAW);
                    gl.EnableVertexAttribArray(1);
                    gl.VertexAttribPointer(1, 3, OpenGL.GL_FLOAT, false, 0, IntPtr.Zero);
                }

                // Texture coordinates
                if (mesh.HasTextureCoords(0))
                {
                    gl.BindBuffer(OpenGL.GL_ARRAY_BUFFER, vboIds[i * 3 + 2]);
                    IntPtr texCoordsPtr = GetIntPtrFromVector3DList(mesh.TextureCoordinateChannels[0].ToList());
                    gl.BufferData(OpenGL.GL_ARRAY_BUFFER, mesh.TextureCoordinateChannels[0].Count * Marshal.SizeOf(typeof(Vector3D)), texCoordsPtr, OpenGL.GL_STATIC_DRAW);
                    gl.EnableVertexAttribArray(2);
                    gl.VertexAttribPointer(2, 2, OpenGL.GL_FLOAT, false, 0, IntPtr.Zero);
                }
            }

            gl.BindBuffer(OpenGL.GL_ARRAY_BUFFER, 0);
            gl.BindVertexArray(0);
        }

        private void CleanupVBOsAndVAOs()
        {
            if (vboIds != null)
            {
                OpenGL gl = openGLControl.OpenGL;
                gl.DeleteBuffers(vboIds.Length, vboIds);
                vboIds = null;
            }

            if (vaoIds != null)
            {
                OpenGL gl = openGLControl.OpenGL;
                gl.DeleteVertexArrays(vaoIds.Length, vaoIds);
                vaoIds = null;
            }
        }

    }
}
