import React, { useEffect, useState } from 'react';
import { Box, LinearProgress, Typography, Paper, Tooltip, CircularProgress } from '@mui/material';
import { useSelector } from 'react-redux';
import { RootState } from '../store';
import { useGetProjectProgressQuery } from '../services/projectService';

interface ProjectProgressBarProps {
  projectId?: string; // Optional project ID, if not provided will use the active project from store
  showDetails?: boolean; // Whether to show detailed progress information
  variant?: 'linear' | 'circular'; // Type of progress indicator to display
  size?: 'small' | 'medium' | 'large'; // Size of the progress bar
}

const ProjectProgressBar: React.FC<ProjectProgressBarProps> = ({
  projectId,
  showDetails = true,
  variant = 'linear',
  size = 'medium',
}) => {
  // Get the active project ID from the store if not provided
  const activeProjectId = useSelector((state: RootState) => state.ui.activeProjectId);
  const effectiveProjectId = projectId || activeProjectId;
  
  // Skip the query if we don't have a project ID
  const { data, error, isLoading, refetch } = useGetProjectProgressQuery(
    effectiveProjectId || 'skip', 
    { skip: !effectiveProjectId }
  );

  // Set up polling for progress updates
  useEffect(() => {
    if (!effectiveProjectId) return;
    
    const intervalId = setInterval(() => {
      refetch();
    }, 10000); // Poll every 10 seconds
    
    return () => clearInterval(intervalId);
  }, [effectiveProjectId, refetch]);

  // Handle loading state
  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', p: 2 }}>
        <CircularProgress size={24} />
        <Typography variant="body2" sx={{ ml: 2 }}>
          Loading project progress...
        </Typography>
      </Box>
    );
  }

  // Handle error state
  if (error) {
    return (
      <Box sx={{ p: 2, color: 'error.main' }}>
        <Typography variant="body2">
          Error loading project progress. Please try again.
        </Typography>
      </Box>
    );
  }

  // Handle no project selected
  if (!effectiveProjectId) {
    return (
      <Box sx={{ p: 2 }}>
        <Typography variant="body2" color="text.secondary">
          No project selected.
        </Typography>
      </Box>
    );
  }

  // Handle no data
  if (!data) {
    return (
      <Box sx={{ p: 2 }}>
        <Typography variant="body2" color="text.secondary">
          No progress data available.
        </Typography>
      </Box>
    );
  }

  const { progress, completedTasks, totalTasks, status, estimatedCompletion } = data;
  
  // Determine progress color based on status
  const getProgressColor = () => {
    switch (status) {
      case 'on_track':
        return 'success.main';
      case 'at_risk':
        return 'warning.main';
      case 'delayed':
        return 'error.main';
      default:
        return 'primary.main';
    }
  };

  // Determine size values
  const getSize = () => {
    switch (size) {
      case 'small':
        return { height: 4, width: '100%', fontSize: 'caption.fontSize' };
      case 'large':
        return { height: 10, width: '100%', fontSize: 'subtitle1.fontSize' };
      default: // medium
        return { height: 8, width: '100%', fontSize: 'body2.fontSize' };
    }
  };

  const sizeValues = getSize();

  // Render circular variant
  if (variant === 'circular') {
    return (
      <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', p: 2 }}>
        <Box position="relative" display="inline-flex">
          <CircularProgress
            variant="determinate"
            value={progress}
            size={size === 'small' ? 40 : size === 'large' ? 80 : 60}
            thickness={4}
            sx={{ color: getProgressColor() }}
          />
          <Box
            sx={{
              top: 0,
              left: 0,
              bottom: 0,
              right: 0,
              position: 'absolute',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <Typography
              variant="caption"
              component="div"
              color="text.secondary"
              fontSize={sizeValues.fontSize}
            >
              {`${Math.round(progress)}%`}
            </Typography>
          </Box>
        </Box>
        
        {showDetails && (
          <Box sx={{ mt: 1, textAlign: 'center' }}>
            <Typography variant="body2" color="text.secondary">
              {completedTasks} of {totalTasks} tasks completed
            </Typography>
            {estimatedCompletion && (
              <Typography variant="caption" color="text.secondary">
                Est. completion: {new Date(estimatedCompletion).toLocaleDateString()}
              </Typography>
            )}
          </Box>
        )}
      </Box>
    );
  }

  // Render linear variant (default)
  return (
    <Paper elevation={1} sx={{ p: 2, borderRadius: 1 }}>
      <Box sx={{ width: '100%' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
          <Typography variant="body1" sx={{ flexGrow: 1 }}>
            Project Progress
          </Typography>
          <Tooltip title={`Status: ${status.replace('_', ' ')}`}>
            <Typography variant="body2" color="text.secondary">
              {Math.round(progress)}%
            </Typography>
          </Tooltip>
        </Box>
        
        <LinearProgress
          variant="determinate"
          value={progress}
          sx={{
            height: sizeValues.height,
            borderRadius: sizeValues.height / 2,
            backgroundColor: 'background.paper',
            '& .MuiLinearProgress-bar': {
              backgroundColor: getProgressColor(),
            },
          }}
        />
        
        {showDetails && (
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 1 }}>
            <Typography variant="body2" color="text.secondary">
              {completedTasks} of {totalTasks} tasks completed
            </Typography>
            {estimatedCompletion && (
              <Typography variant="body2" color="text.secondary">
                Est. completion: {new Date(estimatedCompletion).toLocaleDateString()}
              </Typography>
            )}
          </Box>
        )}
      </Box>
    </Paper>
  );
};

export default ProjectProgressBar;
