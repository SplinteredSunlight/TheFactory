/**
 * Project Master Dashboard Server
 * A simple Express server for serving the dashboard and providing additional functionality
 */

const express = require('express');
const cors = require('cors');
const path = require('path');
const fs = require('fs');
const dotenv = require('dotenv');

// Load environment variables from .env file if present
dotenv.config();

// Create Express app
const app = express();
const PORT = process.env.PORT || 3000;

// Enable CORS
app.use(cors());

// Parse JSON request body
app.use(express.json());

// Serve static files from the current directory
app.use(express.static(__dirname));

// API endpoint for getting configuration
app.get('/api/config', (req, res) => {
  try {
    const configPath = path.join(__dirname, 'config.json');
    const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
    res.json(config);
  } catch (error) {
    console.error('Error reading config:', error);
    res.status(500).json({ error: 'Failed to read configuration' });
  }
});

// API endpoint for updating configuration
app.post('/api/config', (req, res) => {
  try {
    const configPath = path.join(__dirname, 'config.json');
    const config = req.body;
    
    // Validate config
    if (!config.api || !config.scan || !config.ui) {
      return res.status(400).json({ error: 'Invalid configuration format' });
    }
    
    // Write config to file
    fs.writeFileSync(configPath, JSON.stringify(config, null, 2), 'utf8');
    res.json({ success: true });
  } catch (error) {
    console.error('Error updating config:', error);
    res.status(500).json({ error: 'Failed to update configuration' });
  }
});

// API endpoint for scanning directories
app.get('/api/scan', async (req, res) => {
  try {
    const configPath = path.join(__dirname, 'config.json');
    const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
    
    if (!config.scan.enabled) {
      return res.json({ projects: [] });
    }
    
    const projects = [];
    
    // Scan directories for project files
    for (const directory of config.scan.directories) {
      const dirPath = path.resolve(__dirname, '..', directory);
      
      if (!fs.existsSync(dirPath)) {
        console.warn(`Directory not found: ${dirPath}`);
        continue;
      }
      
      // Scan directory for project files
      const files = await scanDirectory(
        dirPath, 
        config.scan.depth, 
        config.scan.includePatterns, 
        config.scan.excludePatterns
      );
      
      // Process found files
      for (const file of files) {
        try {
          const content = fs.readFileSync(file, 'utf8');
          
          // Try to parse as JSON
          try {
            const data = JSON.parse(content);
            if (isProjectFile(data)) {
              projects.push(data);
            }
          } catch (e) {
            // Not a JSON file, check if it's a markdown file with project info
            if (file.endsWith('.md')) {
              const projectInfo = extractProjectInfoFromMarkdown(content);
              if (projectInfo) {
                projects.push(projectInfo);
              }
            }
          }
        } catch (error) {
          console.warn(`Error reading file ${file}:`, error);
        }
      }
    }
    
    res.json({ projects });
  } catch (error) {
    console.error('Error scanning directories:', error);
    res.status(500).json({ error: 'Failed to scan directories' });
  }
});

// Helper function to scan directory recursively
async function scanDirectory(directory, depth, includePatterns, excludePatterns) {
  const files = [];
  
  // Check if we've reached the maximum depth
  if (depth <= 0) {
    return files;
  }
  
  // Read directory contents
  const entries = fs.readdirSync(directory, { withFileTypes: true });
  
  for (const entry of entries) {
    const fullPath = path.join(directory, entry.name);
    
    // Check if path should be excluded
    if (excludePatterns && matchesAnyPattern(entry.name, excludePatterns)) {
      continue;
    }
    
    if (entry.isDirectory()) {
      // Recursively scan subdirectory
      const subFiles = await scanDirectory(
        fullPath, 
        depth - 1, 
        includePatterns, 
        excludePatterns
      );
      files.push(...subFiles);
    } else if (entry.isFile()) {
      // Check if file matches include patterns
      if (!includePatterns || matchesAnyPattern(entry.name, includePatterns)) {
        files.push(fullPath);
      }
    }
  }
  
  return files;
}

// Helper function to check if a string matches any pattern
function matchesAnyPattern(str, patterns) {
  return patterns.some(pattern => {
    // Convert glob pattern to regex
    const regex = new RegExp(
      '^' + 
      pattern
        .replace(/\./g, '\\.')
        .replace(/\*/g, '.*')
        .replace(/\?/g, '.')
      + '$'
    );
    return regex.test(str);
  });
}

// Helper function to check if a JSON object is a project file
function isProjectFile(data) {
  // Check if it has the required properties of a project
  return (
    data && 
    typeof data === 'object' && 
    (
      // Check for task manager project format
      (data.id && data.name && data.phases && data.tasks) ||
      // Check for other project format
      (data.projectId && data.name && data.tasks)
    )
  );
}

// Helper function to extract project info from markdown
function extractProjectInfoFromMarkdown(content) {
  // Simple extraction of project info from markdown
  // This is a basic implementation that can be extended
  
  const titleMatch = content.match(/# (.*)/);
  if (!titleMatch) return null;
  
  const name = titleMatch[1].trim();
  
  // Extract tasks using regex
  const tasks = [];
  const taskMatches = content.matchAll(/- \[([ x])\] (.*)/g);
  
  for (const match of taskMatches) {
    const completed = match[1] === 'x';
    const description = match[2].trim();
    
    tasks.push({
      id: `task-${tasks.length + 1}`,
      name: description,
      description: description,
      status: completed ? 'completed' : 'planned',
      progress: completed ? 100 : 0
    });
  }
  
  if (tasks.length === 0) return null;
  
  // Create a simple project structure
  return {
    id: `md-project-${name.toLowerCase().replace(/[^a-z0-9]/g, '-')}`,
    name: name,
    description: `Project extracted from markdown: ${name}`,
    phases: {
      'phase-1': {
        id: 'phase-1',
        name: 'Tasks',
        description: 'Tasks extracted from markdown',
        order: 0,
        tasks: tasks.map(t => t.id)
      }
    },
    tasks: tasks.reduce((obj, task) => {
      obj[task.id] = task;
      return obj;
    }, {})
  };
}

// Start the server
app.listen(PORT, () => {
  console.log(`Project Master Dashboard server running on http://localhost:${PORT}`);
  console.log(`Open http://localhost:${PORT} in your browser to view the dashboard`);
});
