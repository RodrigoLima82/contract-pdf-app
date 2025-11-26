import React, { } from "react";
import './App.scss';
import { BrowserRouter as Router, Route, Routes } from "react-router-dom";
import {
  Container,
  CssBaseline,
  ThemeProvider,
  createTheme,
} from "@mui/material";
import Header from "./components/Header";
import Summary from "./components/Summary";
import DetailsTable from "./components/DetailsTable";
import PDFResumo from "./components/PDFResumo";
import PDFInfo from "./components/PDFInfo";
import Chatbot from "./components/Chatbot";
import PDFDashboard from "./components/PDFDashboard";
import { ChatbotProvider } from "./components/ChatbotContext";
import { ConsolePage } from './pages/ConsolePage';

// Theme Configuration
const theme = createTheme({
  palette: {
    primary: {
      main: "#FF3621", // Orange 600
    },
    secondary: {
      main: "#1B3139", // Navy 800
    },
    background: {
      default: "#F9F7F4", // Oat Light
    },
    text: {
      primary: "#1B3139", // Navy 800
      secondary: "#555",
    },
  },
  typography: {
    fontFamily: '"DM Sans", Arial, sans-serif',
    h4: {
      fontWeight: 700,
    },
    h6: {
      fontWeight: 500,
      marginBottom: "10px",
    },
    body1: {
      fontSize: "1rem",
      marginBottom: "10px",
    },
    button: {
      textTransform: "none",
    },
  },
  shape: {
    borderRadius: 20,
  },
  spacing: 8,
});

function App() {

  return (
    <ThemeProvider theme={theme} >
      <CssBaseline />
      <ChatbotProvider>
        <Router future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
          <Header />
          <Container style={{ marginTop: "4%", maxWidth: "100%" }}>
            <Routes>
              <Route path="/" element={
                  <>
                    <Summary />
                    <DetailsTable />
                    <PDFDashboard />
                  </>
                }
              />
              <Route path="/resumo/:pdf" element={<PDFResumo />} />
              <Route path="/info/:pdf" element={<PDFInfo />} />
              <Route path="/chat/" element={<div data-component="App"><ConsolePage /></div>} />
            </Routes>
          </Container>
          <Chatbot />
        </Router>
      </ChatbotProvider>
    </ThemeProvider>
  );
}

export default App;
