import React from 'react';
import { Box, Typography, Button } from '@mui/material';
import FolderOpenIcon from '@mui/icons-material/FolderOpen';

function EmptyState({ 
  icon: Icon = FolderOpenIcon, 
  title = "Nenhum dado encontrado",
  description = "Comece fazendo upload de um PDF",
  actionLabel,
  onAction
}) {
  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: 6,
        textAlign: 'center',
      }}
    >
      <Icon sx={{ fontSize: 80, color: '#FF3621', opacity: 0.6, marginBottom: 2 }} />
      <Typography variant="h6" sx={{ color: '#1B3139', fontWeight: 600, marginBottom: 1 }}>
        {title}
      </Typography>
      <Typography variant="body2" sx={{ color: '#555', marginBottom: 3, maxWidth: 400 }}>
        {description}
      </Typography>
      {actionLabel && onAction && (
        <Button
          variant="contained"
          onClick={onAction}
          sx={{
            backgroundColor: '#FF3621',
            '&:hover': { backgroundColor: '#E02F1A' }
          }}
        >
          {actionLabel}
        </Button>
      )}
    </Box>
  );
}

export default EmptyState;

