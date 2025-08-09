diff --git a/README.md b/README.md
index 16ac4f023fc868cf4148c4fb392375b647a52587..bc06bdd332decb270da75e68698a1e5d3dd52ff1 100644
--- a/README.md
+++ b/README.md
@@ -1,2 +1,46 @@
 # HMI-1.00
+Human Machine Interface designer built with PyQt6. This project
+provides a graphical environment for creating and editing industrial
+HMI screens.
+
+## Project goals
+
+- Enable rapid design of HMI screens through an intuitive drag and drop
+  interface.
+- Simplify tag database management for connecting screens with data
+  sources.
+- Allow users to customize themes and appearance for different
+  deployment scenarios.
+
+## Environment prerequisites
+
+- Python 3.11+
+- [PyQt6 6.9.1](https://pypi.org/project/PyQt6/)
+- [qtawesome 1.4.0](https://pypi.org/project/qtawesome/)
+
+## Installation
+
+Install dependencies using the provided `requirements.txt` file:
+
+```bash
+pip install -r requirements.txt
+```
+
+## Launching the application
+
+Run the main entry point to start the editor. Optionally pass a project
+file path to open an existing project.
+
+```bash
+python main.py [project.hmi]
+```
+
+## Key features
+
+- **Screen design** – create and arrange widgets to build interactive
+  operator screens.
+- **Theme selection** – switch between different visual themes to match
+  customer or system requirements.
+- **Tag editing** – manage tag definitions and link them to screen
+  elements for dynamic behavior.
 
