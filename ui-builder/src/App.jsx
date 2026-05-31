import React, { useState } from 'react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { Box, AppBar, Toolbar, Typography, Paper, Button, Container } from '@mui/material';
import DownloadIcon from '@mui/icons-material/Download';
import Form from '@rjsf/mui';
import validator from '@rjsf/validator-ajv8';

// Import our generated JSON Schema!
import rawSchema from './schema.json';

// We want to construct the outer payload {"variable_generation_config": ...}
// Our schema describes the inner object, so we wrap it.
const schema = {
  type: "object",
  properties: {
    variable_generation_config: rawSchema
  },
  required: ["variable_generation_config"]
};

// Create a light theme
const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2',
    },
    background: {
      default: '#f5f5f5',
    },
  },
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
  },
});

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

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box sx={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
        {/* Navbar */}
        <AppBar position="static" elevation={0} sx={{ borderBottom: '1px solid #e0e0e0' }}>
          <Toolbar>
            <Typography variant="h6" component="div" sx={{ flexGrow: 1, fontWeight: 'bold' }}>
              Fauxreal Config Builder
            </Typography>
            <Button 
              variant="contained" 
              color="secondary" 
              startIcon={<DownloadIcon />}
              onClick={downloadJson}
              disableElevation
              sx={{ bgcolor: 'white', color: 'primary.main', '&:hover': { bgcolor: '#f0f0f0' } }}
            >
              Export JSON
            </Button>
          </Toolbar>
        </AppBar>

        {/* Main Content */}
        <Box sx={{ display: 'flex', flexGrow: 1, overflow: 'hidden' }}>
          {/* Left Pane: Form */}
          <Box sx={{ width: '50%', p: 3, overflowY: 'auto' }}>
            <Paper elevation={0} sx={{ p: 4, border: '1px solid #e0e0e0', borderRadius: 2 }}>
              <Typography variant="h5" gutterBottom sx={{ fontWeight: 600 }}>
                Configuration
              </Typography>
              <Typography variant="body2" color="text.secondary" paragraph>
                Use this visual builder to construct your Fauxreal data pipeline. The schema is strictly typed and validated automatically.
              </Typography>
              
              <Form 
                schema={schema} 
                validator={validator}
                formData={formData}
                onChange={(e) => setFormData(e.formData)}
                liveValidate
                showErrorList={false}
              >
                {/* Hide default submit button */}
                <button type="submit" style={{ display: 'none' }}>Submit</button>
              </Form>
            </Paper>
          </Box>

          {/* Right Pane: JSON Preview */}
          <Box sx={{ width: '50%', p: 3, overflowY: 'auto', bgcolor: '#1e1e1e', color: '#d4d4d4' }}>
            <Box sx={{ mb: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
               <Typography variant="overline" sx={{ color: '#858585', fontSize: '0.85rem' }}>
                Live Preview (fauxreal_config.json)
              </Typography>
            </Box>
            <Box 
              component="pre" 
              sx={{ 
                margin: 0, 
                fontFamily: 'monospace', 
                fontSize: '0.9rem',
                whiteSpace: 'pre-wrap',
                wordBreak: 'break-all'
              }}
            >
              {JSON.stringify(formData, null, 2)}
            </Box>
          </Box>
        </Box>
      </Box>
    </ThemeProvider>
  );
}

export default App;
