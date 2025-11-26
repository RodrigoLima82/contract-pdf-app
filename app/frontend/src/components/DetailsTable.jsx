import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Card, CardContent, Table, TableBody, TableCell, TableContainer, 
  TableHead, TableRow, Button, TablePagination, Box, Chip, 
  IconButton, Tooltip, Snackbar, Alert as MuiAlert, CircularProgress,
  Fade, Zoom
} from '@mui/material';
import { styled, keyframes } from '@mui/system';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import VisibilityIcon from '@mui/icons-material/Visibility';
import DescriptionIcon from '@mui/icons-material/Description';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import PendingIcon from '@mui/icons-material/Pending';
import api from "../utils/api";
import TableSkeleton from "./TableSkeleton";
import EmptyState from "./EmptyState";

const slideIn = keyframes`
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
`;

const StyledCard = styled(Card)(({ theme }) => ({
  marginTop: '20px',
  borderRadius: '16px',
  boxShadow: '0 4px 20px rgba(0,0,0,0.08)',
  transition: 'all 0.3s ease',
  '&:hover': {
    boxShadow: '0 8px 30px rgba(0,0,0,0.12)',
  }
}));

const StyledTableCell = styled(TableCell)(({ theme }) => ({
  fontWeight: 700,
  backgroundColor: '#F5F5F5',
  fontSize: 13,
  color: '#1B3139',
  padding: '16px',
  borderBottom: '2px solid #E0E0E0',
}));

const StyledTableRow = styled(TableRow)(({ theme }) => ({
  animation: `${slideIn} 0.4s ease`,
  transition: 'all 0.2s ease',
  '&:hover': {
    backgroundColor: '#FFF8F6',
    boxShadow: '0 2px 8px rgba(255,54,33,0.1)',
  }
}));

const StyledTableCell2 = styled(TableCell)(({ theme }) => ({
  fontSize: 13,
  color: '#555',
  padding: '16px',
}));

const UploadBox = styled(Box)(({ theme }) => ({
  border: '2px dashed #FF3621',
  borderRadius: '12px',
  padding: '32px',
  marginBottom: '24px',
  textAlign: 'center',
  backgroundColor: '#FFF8F6',
  transition: 'all 0.3s ease',
  cursor: 'pointer',
  '&:hover': {
    borderColor: '#E02F1A',
    backgroundColor: '#FFE5E0',
    transform: 'translateY(-2px)',
  }
}));

const ActionButton = styled(Button)(({ theme }) => ({
  fontSize: 11,
  padding: '6px 12px',
  borderRadius: '8px',
  textTransform: 'none',
  fontWeight: 600,
  transition: 'all 0.2s ease',
  borderColor: '#1B3139',
  color: '#1B3139',
  '&:hover': {
    borderColor: '#000',
    backgroundColor: '#F5F5F5',
    transform: 'scale(1.05)',
  }
}));

function DetailsTable() {
  const navigate = useNavigate();
  const [pdfData, setpdfData] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'info' });
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(8);

  const showNotification = (message, severity = 'info') => {
    setSnackbar({ open: true, message, severity });
  };

  const handleCloseSnackbar = () => {
    setSnackbar({ ...snackbar, open: false });
  };

  const handleFileChange = (event) => {
    setSelectedFile(event.target.files[0]);
  };

  const handleUpload = async () => {
    if (!selectedFile) return;
    
    setUploading(true);
    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      await api.post("/api/upload", formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      showNotification('✅ PDF carregado com sucesso! O processamento pode levar de 2 a 5 minutos.', 'success');
      setSelectedFile(null);
      
      // Reload data after 2 seconds
      setTimeout(() => fetchData(), 2000);
    } catch (error) {
      showNotification('❌ Erro ao carregar PDF. Verifique a conexão.', 'error');
    } finally {
      setUploading(false);
    }
  };

  const fetchData = async () => {
    try {
      const response = await api.get("/api/data");
      // Garantir que response.data é um array
      if (Array.isArray(response.data)) {
        setpdfData(response.data);
      } else {
        console.error('Response is not an array:', response.data);
        setpdfData([]);
      }
    } catch (error) {
      console.error('Error fetching data:', error);
      setpdfData([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleChangePage = (event, newPage) => setPage(newPage);
  const handleChangeRowsPerPage = (event) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const paginatedData = pdfData.slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage);

  return (
    <>
      <StyledCard>
        <CardContent>
          <UploadBox onClick={() => document.getElementById('file-input').click()}>
            <CloudUploadIcon sx={{ fontSize: 48, color: '#FF3621', marginBottom: 2 }} />
            <Box sx={{ fontSize: 16, fontWeight: 600, color: '#1B3139', marginBottom: 1 }}>
              {selectedFile ? selectedFile.name : 'Clique para selecionar um PDF'}
            </Box>
            {selectedFile && (
              <Fade in={true}>
                <Box sx={{ fontSize: 13, color: '#555', marginTop: 1 }}>
                  Tipo: {selectedFile.type} • Tamanho: {(selectedFile.size / 1024).toFixed(2)} KB
                </Box>
              </Fade>
            )}
            <input
              id="file-input"
              type="file"
              accept=".pdf"
              onChange={handleFileChange}
              style={{ display: 'none' }}
            />
          </UploadBox>

          {selectedFile && (
            <Zoom in={true}>
              <Button
                variant="contained"
                fullWidth
                onClick={handleUpload}
                disabled={uploading}
                startIcon={uploading ? <CircularProgress size={20} color="inherit" /> : <CloudUploadIcon />}
                sx={{
                  backgroundColor: '#FF3621',
                  marginBottom: 3,
                  padding: '12px',
                  fontSize: 14,
                  fontWeight: 600,
                  borderRadius: '10px',
                  '&:hover': { backgroundColor: '#E02F1A' },
                  '&:disabled': { backgroundColor: '#CCC' }
                }}
              >
                {uploading ? 'Enviando...' : 'Carregar Arquivo'}
              </Button>
            </Zoom>
          )}

          {loading ? (
            <TableSkeleton rows={5} columns={10} />
          ) : pdfData.length === 0 ? (
            <EmptyState
              title="Nenhum PDF encontrado"
              description="Faça upload do seu primeiro PDF para começar"
              actionLabel="Selecionar PDF"
              onAction={() => document.getElementById('file-input').click()}
            />
          ) : (
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <StyledTableCell>Nome do Arquivo</StyledTableCell>
                    <StyledTableCell>Tipo</StyledTableCell>
                    <StyledTableCell>Tamanho</StyledTableCell>
                    <StyledTableCell>Status</StyledTableCell>
                    <StyledTableCell>Upload</StyledTableCell>
                    <StyledTableCell>Processado</StyledTableCell>
                    <StyledTableCell align="center">Ações</StyledTableCell>
                  </TableRow>
                </TableHead>

                <TableBody>
                  {paginatedData.map((pdf, index) => (
                    <StyledTableRow key={pdf.file_name} style={{ animationDelay: `${index * 0.05}s` }}>
                      <StyledTableCell2>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <DescriptionIcon sx={{ fontSize: 20, color: '#FF3621' }} />
                          <span style={{ fontWeight: 600 }}>{pdf.file_name}</span>
                        </Box>
                      </StyledTableCell2>
                      <StyledTableCell2>
                        <Chip label={pdf.type} size="small" sx={{ fontSize: 11 }} />
                      </StyledTableCell2>
                      <StyledTableCell2>{pdf.size} KB</StyledTableCell2>
                      <StyledTableCell2>
                        <Chip
                          icon={pdf.processed === '✅' ? <CheckCircleIcon /> : <PendingIcon />}
                          label={pdf.processed === '✅' ? 'Processado' : 'Pendente'}
                          size="small"
                          color={pdf.processed === '✅' ? 'success' : 'default'}
                          sx={{ fontSize: 11, fontWeight: 600 }}
                        />
                      </StyledTableCell2>
                      <StyledTableCell2>{pdf.upload_time}</StyledTableCell2>
                      <StyledTableCell2>{pdf.processed_time}</StyledTableCell2>
                      <StyledTableCell2>
                        <Box sx={{ display: 'flex', gap: 1, justifyContent: 'center', flexWrap: 'wrap' }}>
                          <Tooltip title="Ver Detalhes">
                            <span>
                              <ActionButton
                                size="small"
                                onClick={() => navigate(`/info/${pdf.file_name}`)}
                                disabled={pdf.processed === '❌'}
                                startIcon={<VisibilityIcon sx={{ fontSize: 16 }} />}
                              >
                                Detalhes
                              </ActionButton>
                            </span>
                          </Tooltip>

                          <Tooltip title="Ver Resumo">
                            <span>
                              <ActionButton
                                size="small"
                                onClick={() => navigate(`/resumo/${pdf.file_name}`)}
                                disabled={pdf.processed === '❌'}
                                startIcon={<DescriptionIcon sx={{ fontSize: 16 }} />}
                              >
                                Resumo
                              </ActionButton>
                            </span>
                          </Tooltip>
                        </Box>
                      </StyledTableCell2>
                    </StyledTableRow>
                  ))}
                </TableBody>
              </Table>
              <TablePagination
                component="div"
                count={pdfData.length}
                page={page}
                onPageChange={handleChangePage}
                rowsPerPage={rowsPerPage}
                onRowsPerPageChange={handleChangeRowsPerPage}
                rowsPerPageOptions={[8, 10, 25]}
                labelRowsPerPage="Linhas por página:"
                labelDisplayedRows={({ from, to, count }) => `${from}-${to} de ${count}`}
              />
            </TableContainer>
          )}
        </CardContent>
      </StyledCard>

      <Snackbar
        open={snackbar.open}
        autoHideDuration={5000}
        onClose={handleCloseSnackbar}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <MuiAlert
          onClose={handleCloseSnackbar}
          severity={snackbar.severity}
          variant="filled"
          sx={{ minWidth: '300px', borderRadius: '10px', fontWeight: 600 }}
        >
          {snackbar.message}
        </MuiAlert>
      </Snackbar>
    </>
  );
}

export default DetailsTable;
