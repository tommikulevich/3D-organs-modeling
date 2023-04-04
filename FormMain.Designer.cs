namespace MSN_GUI
{
    partial class FormMSN
    {
        /// <summary>
        ///  Required designer variable.
        /// </summary>
        private System.ComponentModel.IContainer components = null;

        /// <summary>
        ///  Clean up any resources being used.
        /// </summary>
        /// <param name="disposing">true if managed resources should be disposed; otherwise, false.</param>
        protected override void Dispose(bool disposing)
        {
            if (disposing && (components != null))
            {
                components.Dispose();
            }
            base.Dispose(disposing);
        }

        #region Windows Form Designer generated code

        /// <summary>
        ///  Required method for Designer support - do not modify
        ///  the contents of this method with the code editor.
        /// </summary>
        private void InitializeComponent()
        {
            openFileDialog = new OpenFileDialog();
            menuStrip1 = new MenuStrip();
            chooseObjToolStripMenuItem = new ToolStripMenuItem();
            helpToolStripMenuItem = new ToolStripMenuItem();
            openGLControlMain = new SharpGL.OpenGLControl();
            menuStrip1.SuspendLayout();
            ((System.ComponentModel.ISupportInitialize)openGLControlMain).BeginInit();
            SuspendLayout();
            // 
            // openFileDialog
            // 
            openFileDialog.FileName = "openFileDialog";
            // 
            // menuStrip1
            // 
            menuStrip1.ImageScalingSize = new Size(32, 32);
            menuStrip1.Items.AddRange(new ToolStripItem[] { chooseObjToolStripMenuItem, helpToolStripMenuItem });
            menuStrip1.Location = new Point(0, 0);
            menuStrip1.Name = "menuStrip1";
            menuStrip1.Size = new Size(1340, 40);
            menuStrip1.TabIndex = 1;
            menuStrip1.Text = "menuStrip1";
            // 
            // chooseObjToolStripMenuItem
            // 
            chooseObjToolStripMenuItem.Name = "chooseObjToolStripMenuItem";
            chooseObjToolStripMenuItem.Size = new Size(184, 36);
            chooseObjToolStripMenuItem.Text = "Select .obj file";
            chooseObjToolStripMenuItem.Click += chooseObjToolStripMenuItem_Click;
            // 
            // helpToolStripMenuItem
            // 
            helpToolStripMenuItem.Name = "helpToolStripMenuItem";
            helpToolStripMenuItem.Size = new Size(84, 36);
            helpToolStripMenuItem.Text = "Help";
            helpToolStripMenuItem.Click += helpToolStripMenuItem_Click;
            // 
            // openGLControlMain
            // 
            openGLControlMain.Dock = DockStyle.Fill;
            openGLControlMain.DrawFPS = true;
            openGLControlMain.FrameRate = 60;
            openGLControlMain.Location = new Point(0, 40);
            openGLControlMain.Margin = new Padding(6, 7, 6, 7);
            openGLControlMain.Name = "openGLControlMain";
            openGLControlMain.OpenGLVersion = SharpGL.Version.OpenGLVersion.OpenGL2_1;
            openGLControlMain.RenderContextType = SharpGL.RenderContextType.FBO;
            openGLControlMain.RenderTrigger = SharpGL.RenderTrigger.TimerBased;
            openGLControlMain.Size = new Size(1340, 689);
            openGLControlMain.TabIndex = 2;
            // 
            // FormMSN
            // 
            AutoScaleDimensions = new SizeF(13F, 32F);
            AutoScaleMode = AutoScaleMode.Font;
            AutoSize = true;
            ClientSize = new Size(1340, 729);
            Controls.Add(openGLControlMain);
            Controls.Add(menuStrip1);
            MainMenuStrip = menuStrip1;
            Name = "FormMSN";
            Text = "Project MSN";
            Load += FormMain_Load;
            menuStrip1.ResumeLayout(false);
            menuStrip1.PerformLayout();
            ((System.ComponentModel.ISupportInitialize)openGLControlMain).EndInit();
            ResumeLayout(false);
            PerformLayout();
        }

        #endregion
        private OpenFileDialog openFileDialog;
        private MenuStrip menuStrip1;
        private ToolStripMenuItem chooseObjToolStripMenuItem;
        private ToolStripMenuItem helpToolStripMenuItem;
        private SharpGL.OpenGLControl openGLControlMain;
    }
}