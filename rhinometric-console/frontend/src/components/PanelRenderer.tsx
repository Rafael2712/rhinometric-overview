import React, { useState } from 'react';
import { Box, Typography, CircularProgress, Alert, IconButton } from '@mui/material';
import RefreshIcon from '@mui/icons-material/Refresh';

interface PanelRendererProps {
  uid: string;
  panelId: number;
  title: string;
  from: string;
  to: string;
}

export const PanelRenderer: React.FC<PanelRendererProps> = ({
  uid,
  panelId,
  title,
  from,
  to,
}) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);

  const imageUrl = `/api/dashboards/${uid}/panels/${panelId}/render?from=${from}&to=${to}&width=1200&height=400&_=${refreshKey}`;

  const handleImageLoad = () => {
    setLoading(false);
    setError(false);
  };

  const handleImageError = () => {
    setLoading(false);
    setError(true);
  };

  const handleRefresh = () => {
    setLoading(true);
    setError(false);
    setRefreshKey(prev => prev + 1);
  };

  return (
    <Box p={2} position="relative">
      {/* Panel Title */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
        <Typography variant="h6" fontSize={14} fontWeight={500}>
          {title}
        </Typography>
        <IconButton size="small" onClick={handleRefresh} disabled={loading}>
          <RefreshIcon fontSize="small" />
        </IconButton>
      </Box>

      {/* Loading State */}
      {loading && (
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="300px">
          <CircularProgress size={30} />
        </Box>
      )}

      {/* Error State */}
      {error && !loading && (
        <Alert severity="error" sx={{ mb: 2 }}>
          Failed to load panel
        </Alert>
      )}

      {/* Image */}
      <Box
        component="img"
        src={imageUrl}
        alt={title}
        onLoad={handleImageLoad}
        onError={handleImageError}
        sx={{
          width: '100%',
          height: 'auto',
          display: loading || error ? 'none' : 'block',
          borderRadius: 1,
        }}
      />
    </Box>
  );
};
