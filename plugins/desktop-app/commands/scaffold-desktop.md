Scaffold a desktop application using Electron or Tauri with proper project structure.

## Steps


1. Choose the framework based on requirements:
2. Initialize the project:
3. Set up the project structure:
4. Configure window management:
5. Set up IPC (Inter-Process Communication):
6. Add platform-specific features:
7. Configure build and packaging:

## Format


```
App: <name>
Framework: <Electron|Tauri>
Frontend: <React|Vue|Svelte|Vanilla>
Structure:
```


## Rules

- Never expose Node.js APIs directly to the renderer (use preload/IPC).
- Enable context isolation and disable node integration in renderer.
- Use auto-updater for production distribution.

