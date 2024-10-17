import { createAsyncThunk, createSlice } from "@reduxjs/toolkit";
import axios from "axios";

export const fetchProducts = createAsyncThunk("fetch/products/", async () => {
  const res = await axios.get("https://10e9-51-210-71-107.ngrok-free.app/store/products/", {
    headers: {
      "ngrok-skip-browser-warning": true,
    },
  });
  return res.data.results;
});

export const ProductsStateManagement = createSlice({
  name: "products",
  initialState: {
    productsData: null,
    loading: null,
    error: null,
  },
  extraReducers: (Builder) => [
    Builder.addCase(fetchProducts.fulfilled, (state, action) => {
      state.productsData = action.payload;
      state.loading = false;
      state.error = null;
    })
      .addCase(fetchProducts.pending, (state) => {
        // state.productsData = null;
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchProducts.rejected, (state, action) => {
        // state.productsData = null;
        state.loading = true;
        state.error = action.error.message;
      }),
  ],
});
export default ProductsStateManagement.reducer;
