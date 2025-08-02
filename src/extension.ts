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
  statusBarItem.command = 'codebase-dumper.generateRooReview';
  statusBarItem.text = `$(file-zip) RooReview`;
  statusBarItem.tooltip = 'Generate a RooReview for the current project';
  statusBarItem.show();
  context.subscriptions.push(statusBarItem);

  // --- Register the Commands ---
  const dumpCodebase = vscode.commands.registerCommand(
    'codebase-dumper.dumpCodebase',
    (uri?: vscode.Uri) => {
      runPythonScript(context, 'dump_codebase.py', uri, 'Dumping Codebase...', [
        '--prompt=neutral',
      ]);
    },
  );

  const generateRooReview = vscode.commands.registerCommand(
    'codebase-dumper.generateRooReview',
    (uri?: vscode.Uri) => {
      runPythonScript(
        context,
        'dump_codebase.py',
        uri,
        'Generating RooReview...',
        ['--prompt=rooreview'],
      );
    },
  );

  const rooreviewAuditor = vscode.commands.registerCommand(
    'codebase-dumper.rooreviewAuditor',
    (uri?: vscode.Uri) => {
      runPythonScript(
        context,
        'dump_codebase.py',
        uri,
        'Auditing RooReview...',
        ['--prompt=rooreview_auditor'],
      );
    },
  );

  const codebaseAuditor = vscode.commands.registerCommand(
    'codebase-dumper.codebaseAuditor',
    (uri?: vscode.Uri) => {
      runPythonScript(
        context,
        'dump_codebase.py',
        uri,
        'Auditing Codebase...',
        ['--prompt=codebase_auditor'],
      );
    },
  );

  const documentationAuditor = vscode.commands.registerCommand(
    'codebase-dumper.documentationAuditor',
    (uri?: vscode.Uri) => {
      runPythonScript(
        context,
        'dump_codebase.py',
        uri,
        'Auditing Documentation...',
        ['--prompt=documentation_auditor'],
      );
    },
  );

  const featureArchitect = vscode.commands.registerCommand(
    'codebase-dumper.featureArchitect',
    (uri?: vscode.Uri) => {
      runPythonScript(
        context,
        'dump_codebase.py',
        uri,
        'Starting Feature Architect Session...',
        ['--prompt=feature_architect'],
      );
    },
  );

  const dumpDiff = vscode.commands.registerCommand(
    'codebase-dumper.dumpDiff',
    (uri?: vscode.Uri) => {
      runPythonScript(context, 'dump_diff.py', uri, 'Dumping Git Diffs...');
    },
  );

  context.subscriptions.push(
    dumpCodebase,
    generateRooReview,
    rooreviewAuditor,
    codebaseAuditor,
    documentationAuditor,
    featureArchitect,
    dumpDiff,
  );

  // --- Add Status Bar Item for the Diff Command ---
  const diffStatusBarItem = vscode.window.createStatusBarItem(
    vscode.StatusBarAlignment.Right,
    99,
  );
  diffStatusBarItem.command = 'codebase-dumper.dumpDiff';
  diffStatusBarItem.text = `$(diff) Dump Diffs`;
  diffStatusBarItem.tooltip = 'Dump Git diffs to a text file';
  diffStatusBarItem.show();
  context.subscriptions.push(diffStatusBarItem);
}

function runPythonScript(
  context: vscode.ExtensionContext,
  scriptName: string,
  uri: vscode.Uri | undefined,
  title: string,
  args: string[] = [],
) {
  let projectRoot: string | undefined;

  const determineRootAndExecute = (p: string) => {
    vscode.workspace.fs.stat(vscode.Uri.file(p)).then((stats) => {
      const finalRoot =
        stats.type === vscode.FileType.Directory ? p : path.dirname(p);
      executeScript(finalRoot);
    });
  };

  if (uri) {
    determineRootAndExecute(uri.fsPath);
  } else {
    const workspaceFolders = vscode.workspace.workspaceFolders;
    if (workspaceFolders && workspaceFolders.length > 0) {
      determineRootAndExecute(workspaceFolders[0].uri.fsPath);
    } else {
      vscode.window.showErrorMessage(
        'No project folder found. Open a folder or right-click one.',
      );
    }
  }

  function executeScript(cwd: string) {
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
          const pythonProcess = spawn('python', [pythonScriptPath, ...args], {
            cwd: cwd,
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
}

// This function is called when your extension is deactivated
export function deactivate() {}