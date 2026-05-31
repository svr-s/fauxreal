import React, { useState } from 'react';
import Form from '@rjsf/core';
import validator from '@rjsf/validator-ajv8';
import { Download, GitBranch, Code2, Database } from 'lucide-react';
import Editor from '@monaco-editor/react';

import rawSchema from './schema.json';
import { CustomFieldTemplate, CustomObjectFieldTemplate, CustomArrayFieldTemplate } from './templates';

// Recursive function to strip {type: "null"} from anyOf arrays in the schema
// This prevents RJSF from rendering annoying "Option 1 / Option 2" dropdowns for Optional fields.
function stripNullTypes(obj) {
  if (Array.isArray(obj)) {
    return obj.map(stripNullTypes);
  } else if (obj !== null && typeof obj === 'object') {
    const newObj = {};
    for (const [key, value] of Object.entries(obj)) {
      if (key === 'anyOf' && Array.isArray(value)) {
        // Filter out the null types
        const filtered = value.filter(item => item.type !== 'null');
        if (filtered.length === 1) {
          // If only one type is left, just merge it into the object instead of using anyOf
          Object.assign(newObj, stripNullTypes(filtered[0]));
        } else {
          newObj[key] = stripNullTypes(filtered);
        }
      } else {
        newObj[key] = stripNullTypes(value);
      }
    }
    return newObj;
  }
  return obj;
}

const cleanedSchema = stripNullTypes(rawSchema);
const { $defs, ...restSchema } = cleanedSchema;

const schema = {
  type: "object",
  $defs: $defs,
  properties: {
    fauxreal_config: restSchema
  },
  required: ["fauxreal_config"]
};

function App() {
  const [formData, setFormData] = useState({});

  const downloadJson = () => {
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(formData, null, 2));
    const downloadAnchorNode = document.createElement('a');
    downloadAnchorNode.setAttribute("href", dataStr);
    downloadAnchorNode.setAttribute("download", "fauxreal_config.json");
    document.body.appendChild(downloadAnchorNode);
    downloadAnchorNode.click();
    downloadAnchorNode.remove();
  };

  const handleEditorChange = (value) => {
    try {
      const parsed = JSON.parse(value);
      setFormData(parsed);
    } catch (e) {
      // Ignore parse errors while typing
    }
  };

  return (
    <div className="flex flex-col h-screen overflow-hidden">
      {/* Header */}
      <header className="flex-none border-b border-[var(--color-border)] bg-[var(--color-surface)] px-6 py-4 flex items-center justify-between z-10">
        <div className="flex items-center gap-3">
          <div className="bg-gradient-to-br from-purple-500 to-indigo-600 p-2 rounded-lg text-white shadow-lg">
            <Database size={24} />
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight text-white">Fauxreal Builder</h1>
            <p className="text-xs text-[var(--color-text-muted)]">Visual JSON Schema Editor</p>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <a 
            href="https://github.com/svr-s/fauxreal" 
            target="_blank" 
            rel="noopener noreferrer"
            className="text-[var(--color-text-muted)] hover:text-white transition-colors"
          >
            <GitBranch size={20} />
          </a>
          <button 
            onClick={downloadJson}
            className="flex items-center gap-2 bg-[var(--color-primary)] hover:bg-[var(--color-primary-hover)] text-white px-4 py-2 rounded-md font-medium text-sm transition-all shadow-lg shadow-purple-500/20"
          >
            <Download size={16} />
            Export JSON
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 flex overflow-hidden">
        {/* Left Pane - Form */}
        <div className="w-1/2 overflow-y-auto p-6 border-r border-[var(--color-border)] form-container">
          <div className="glass-panel p-6 max-w-3xl mx-auto">
            <div className="mb-6 border-b border-[var(--color-border)] pb-4">
              <h2 className="text-lg font-semibold text-white flex items-center gap-2">
                <Code2 size={18} className="text-[var(--color-primary)]" />
                Configuration Builder
              </h2>
              <p className="text-sm text-[var(--color-text-muted)] mt-1">
                Construct your Fauxreal data pipeline visually. The schema is strictly typed and validated.
              </p>
            </div>
            
            <Form 
              schema={schema} 
              validator={validator}
              formData={formData}
              onChange={(e) => setFormData(e.formData)}
              liveValidate
              showErrorList={false}
              templates={{
                FieldTemplate: CustomFieldTemplate,
                ObjectFieldTemplate: CustomObjectFieldTemplate,
                ArrayFieldTemplate: CustomArrayFieldTemplate
              }}
            >
              <button type="submit" className="hidden">Submit</button>
            </Form>
          </div>
        </div>

        {/* Right Pane - Monaco Editor */}
        <div className="w-1/2 flex flex-col bg-[#1e1e1e]">
          <div className="flex-none px-4 py-2 border-b border-[var(--color-border)] bg-[var(--color-surface)] flex justify-between items-center">
            <span className="text-xs font-mono text-[var(--color-text-muted)]">fauxreal_config.json</span>
          </div>
          <div className="flex-1">
            <Editor
              height="100%"
              defaultLanguage="json"
              theme="vs-dark"
              value={JSON.stringify(formData, null, 2)}
              onChange={handleEditorChange}
              options={{
                minimap: { enabled: false },
                fontSize: 14,
                wordWrap: 'on',
                formatOnPaste: true,
                scrollBeyondLastLine: false,
                padding: { top: 16 }
              }}
            />
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
