import open3d as o3d

mesh = o3d.io.read_triangle_mesh("Example OBJ/segmentation_spleen_16.obj")
mesh.compute_vertex_normals()
vertices = mesh.vertices
vertex_colors = mesh.vertex_colors
o3d.visualization.draw_geometries([mesh])