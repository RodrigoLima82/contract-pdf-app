import React, { useState, useEffect } from 'react';
import api from '../utils/api';

function PDFViewer (pdf) {
  const [pdfBlob, setPdfBlob] = useState(null);

  useEffect(() => {
    const fetchPDF = async () => {
      try {

        const response = await api.get('/api/pdf', { 
          params: {
            pdf: pdf['pdf']
          },
          responseType: 'blob' 
        });
        setPdfBlob(response.data);
      } catch (error) {
        console.error('Error fetching PDF:', error);
      }
    };

    fetchPDF();
  }, []);

  if (!pdfBlob) {
    return <div>Loading PDF...</div>;
  }

  const pdfUrl = URL.createObjectURL(pdfBlob);

  return (
    <iframe id={pdf['pdf']} src={pdfUrl} width="100%" height="600px" />
  );
}

export default PDFViewer;