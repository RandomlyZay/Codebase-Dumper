import * as vscode from 'vscode';
import * as path from 'path';
import { spawn } from 'child_process';

// This function is called when your extension is activated
export function activate(context: vscode.ExtensionContext) {

    // --- Create the Status Bar Item ---
    const statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 100);
    statusBarItem.command = 'codebase-dumper.dumpCodebase';
    statusBarItem.text = `$(file-zip) Dump Codebase`;
    statusBarItem.tooltip = 'Run Codebase Dumper on the current project';
    statusBarItem.show();
    context.subscriptions.push(statusBarItem);


    // --- Register the Command ---
    // The command can be triggered by the Command Palette, the status bar, or a right-click.
    // The 'uri' argument is provided by VS Code when run from a context menu.
    let disposable = vscode.commands.registerCommand('codebase-dumper.dumpCodebase', (uri?: vscode.Uri) => {

        let projectRoot: string | undefined;

        if (uri) {
            // If 'uri' exists, the command was run from the Explorer context menu.
            projectRoot = uri.fsPath;
        } else {
            // Otherwise, find the root of the currently open project.
            const workspaceFolders = vscode.workspace.workspaceFolders;
            if (workspaceFolders && workspaceFolders.length > 0) {
                projectRoot = workspaceFolders[0].uri.fsPath;
            }
        }
        
        if (!projectRoot) {
            vscode.window.showErrorMessage('No project folder found. Open a folder or right-click one.');
            return;
        }

        // Path to the Python script within your extension's folder
        const pythonScriptPath = path.join(context.extensionPath, 'scripts', 'dump_codebase.py');

        vscode.window.withProgress({
            location: vscode.ProgressLocation.Notification,
            title: "Dumping codebase...",
            cancellable: false
        }, (progress) => {
            
            const p = new Promise<void>(resolve => {
                
                // We run the script from the determined project's root directory.
                const pythonProcess = spawn('python', [pythonScriptPath], {
                    cwd: projectRoot,
                    env: { ...process.env, 'PYTHONIOENCODING': 'utf-8' }
                });

                let stdout = '';
                let stderr = '';

                pythonProcess.stdout.on('data', (data) => {
                    stdout += data.toString();
                });

                pythonProcess.stderr.on('data', (data) => {
                    stderr += data.toString();
                });

                pythonProcess.on('close', (code) => {
                    if (code === 0) {
                        vscode.window.showInformationMessage(stdout.trim());
                    } else {
                        vscode.window.showErrorMessage(`Error dumping codebase: ${stderr}`);
                    }
                    resolve();
                });

                pythonProcess.on('error', (err) => {
                    vscode.window.showErrorMessage(`Failed to start script: ${err.message}`);
                    resolve();
                });
            });

            return p;
        });
    });

    context.subscriptions.push(disposable);
}

// This function is called when your extension is deactivated
export function deactivate() {}