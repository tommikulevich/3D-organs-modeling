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
            openGLControlMain = new SharpGL.OpenGLControl();
            openFileDialog = new OpenFileDialog();
            menuStrip1 = new MenuStrip();
            chooseObjToolStripMenuItem = new ToolStripMenuItem();
            helpToolStripMenuItem = new ToolStripMenuItem();
            ((System.ComponentModel.ISupportInitialize)openGLControlMain).BeginInit();
            menuStrip1.SuspendLayout();
            SuspendLayout();
            // 
            // openGLControlMain
            // 
            openGLControlMain.DrawFPS = false;
            openGLControlMain.Location = new Point(15, 47);
            openGLControlMain.Margin = new Padding(6, 7, 6, 7);
            openGLControlMain.Name = "openGLControlMain";
            openGLControlMain.OpenGLVersion = SharpGL.Version.OpenGLVersion.OpenGL2_1;
            openGLControlMain.RenderContextType = SharpGL.RenderContextType.DIBSection;
            openGLControlMain.RenderTrigger = SharpGL.RenderTrigger.TimerBased;
            openGLControlMain.Size = new Size(1127, 716);
            openGLControlMain.TabIndex = 0;
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
            menuStrip1.Size = new Size(1157, 40);
            menuStrip1.TabIndex = 1;
            menuStrip1.Text = "menuStrip1";
            // 
            // chooseObjToolStripMenuItem
            // 
            chooseObjToolStripMenuItem.Name = "chooseObjToolStripMenuItem";
            chooseObjToolStripMenuItem.Size = new Size(211, 36);
            chooseObjToolStripMenuItem.Text = "Wybierz plik .obj";
            chooseObjToolStripMenuItem.Click += chooseObjToolStripMenuItem_Click;
            // 
            // helpToolStripMenuItem
            // 
            helpToolStripMenuItem.Name = "helpToolStripMenuItem";
            helpToolStripMenuItem.Size = new Size(106, 36);
            helpToolStripMenuItem.Text = "Pomóc";
            helpToolStripMenuItem.Click += helpToolStripMenuItem_Click;
            // 
            // FormMSN
            // 
            AutoScaleDimensions = new SizeF(13F, 32F);
            AutoScaleMode = AutoScaleMode.Font;
            ClientSize = new Size(1157, 779);
            Controls.Add(menuStrip1);
            Controls.Add(openGLControlMain);
            MainMenuStrip = menuStrip1;
            Name = "FormMSN";
            Text = "Projekt MSN";
            Load += FormMain_Load;
            ((System.ComponentModel.ISupportInitialize)openGLControlMain).EndInit();
            menuStrip1.ResumeLayout(false);
            menuStrip1.PerformLayout();
            ResumeLayout(false);
            PerformLayout();
        }

        #endregion

        private SharpGL.OpenGLControl openGLControlMain;
        private OpenFileDialog openFileDialog;
        private MenuStrip menuStrip1;
        private ToolStripMenuItem chooseObjToolStripMenuItem;
        private ToolStripMenuItem helpToolStripMenuItem;
    }
}