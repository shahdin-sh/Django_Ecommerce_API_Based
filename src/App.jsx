import { BrowserRouter, Route, Routes } from "react-router-dom";
import Header from "./Components/Header/Header";
import ProductsPage from "./Pages/ProductsPage/ProductsPage";
import HomePage from "./Pages/HomePage/HomePage";
import Footer from "./Components/Footer/Footer";

const App = () => {
  return (
    <>
      <BrowserRouter>
        <Header />
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/products" element={<ProductsPage />} />
        </Routes>
        <Footer/>
      </BrowserRouter>
    </>
  );
};

export default App;
