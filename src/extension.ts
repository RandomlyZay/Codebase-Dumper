import * as vscode from 'vscode';
import * as path from 'path';
import { spawn } from 'child_process';

// This function is called when your extension is activated
export function activate(context: vscode.ExtensionContext) {
  // --- Create the Status Bar Item ---
  const statusBarItem = vscode.window.createStatusBarItem(
    vscode.StatusBarAlignment.Right,
    100,
  );
  statusBarItem.command = 'codebase-dumper.dumpCodebase';
  statusBarItem.text = `$(file-zip) Dump Codebase`;
  statusBarItem.tooltip = 'Run Codebase Dumper on the current project';
  statusBarItem.show();
  context.subscriptions.push(statusBarItem);

  // --- Register the Commands ---
  // The 'uri' argument is provided by VS Code when run from a context menu.
  const dumpCodebaseDisposable = vscode.commands.registerCommand(
    'codebase-dumper.dumpCodebase',
    (uri?: vscode.Uri) => {
      runPythonScript(context, 'dump_codebase.py', uri, 'Dumping codebase...');
    },
  );

  const dumpCodebaseWithoutPromptDisposable = vscode.commands.registerCommand(
    'codebase-dumper.dumpCodebaseWithoutPrompt',
    (uri?: vscode.Uri) => {
      runPythonScript(
        context,
        'dump_codebase.py',
        uri,
        'Dumping codebase (no prompt)...',
        ['--no-prompt'],
      );
    },
  );

  const dumpDiffDisposable = vscode.commands.registerCommand(
    'codebase-dumper.dumpDiff',
    (uri?: vscode.Uri) => {
      runPythonScript(context, 'dump_diff.py', uri, 'Dumping code diff...');
    },
  );

  const dumpDiffWithoutPromptDisposable = vscode.commands.registerCommand(
    'codebase-dumper.dumpDiffWithoutPrompt',
    (uri?: vscode.Uri) => {
      runPythonScript(
        context,
        'dump_diff.py',
        uri,
        'Dumping code diff (no prompt)...',
        ['--no-prompt'],
      );
    },
  );

  context.subscriptions.push(
    dumpCodebaseDisposable,
    dumpCodebaseWithoutPromptDisposable,
    dumpDiffDisposable,
    dumpDiffWithoutPromptDisposable,
  );

  // --- Add Status Bar Item for the Diff Command ---
  const diffStatusBarItem = vscode.window.createStatusBarItem(
    vscode.StatusBarAlignment.Right,
    99,
  );
  diffStatusBarItem.command = 'codebase-dumper.dumpDiff';
  diffStatusBarItem.text = `$(diff) Dump Diff`;
  diffStatusBarItem.tooltip = 'Dump a Git diff to a text file';
  diffStatusBarItem.show();
  context.subscriptions.push(diffStatusBarItem);
}

function runPythonScript(
  context: vscode.ExtensionContext,
  scriptName: string,
  uri: vscode.Uri | undefined,
  title: string,
  args: string[] = [], // ✅ Add args parameter
) {
  let projectRoot: string | undefined;

  if (uri) {
    projectRoot = uri.fsPath;
  } else {
    const workspaceFolders = vscode.workspace.workspaceFolders;
    if (workspaceFolders && workspaceFolders.length > 0) {
      projectRoot = workspaceFolders[0].uri.fsPath;
    }
  }

  if (!projectRoot) {
    vscode.window.showErrorMessage(
      'No project folder found. Open a folder or right-click one.',
    );
    return;
  }

  const pythonScriptPath = path.join(
    context.extensionPath,
    'scripts',
    scriptName,
  );

  vscode.window.withProgress(
    {
      location: vscode.ProgressLocation.Notification,
      title: title,
      cancellable: false,
    },
    (progress) => {
      const p = new Promise<void>((resolve) => {
        // ✅ Pass the args to the spawn command
        const pythonProcess = spawn('python', [pythonScriptPath, ...args], {
          cwd: projectRoot,
          env: { ...process.env, PYTHONIOENCODING: 'utf-8' },
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
            vscode.window.showInformationMessage(
              stdout.trim() || 'Action completed successfully.',
            );
          } else {
            vscode.window.showErrorMessage(`Error: ${stderr}`);
          }
          resolve();
        });

        pythonProcess.on('error', (err) => {
          vscode.window.showErrorMessage(
            `Failed to start script: ${err.message}`,
          );
          resolve();
        });
      });
      return p;
    },
  );
}

// This function is called when your extension is deactivated
export function deactivate() {}