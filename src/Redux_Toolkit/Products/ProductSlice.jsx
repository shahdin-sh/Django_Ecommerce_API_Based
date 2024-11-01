import { createAsyncThunk, createSlice } from "@reduxjs/toolkit";
import axios from "axios";

export const getProduct = createAsyncThunk("/get/product", async (name) => {
  const res = await axios.get(`http://0.0.0.0:8000/store/products/${name}`, {
    // headers: {
    //   "ngrok-skip-browser-warning": true,
    // },
  });
  return res.data;
});

export const productData = createSlice({
  name: "product",
  initialState: {
    productData: null,
    loading: true,
    error: null,
  },
  extraReducers: (Builder) => {
    Builder.addCase(getProduct.fulfilled, (state, action) => {
      state.productData = action.payload;
      state.loading = false;
      state.error = null;
    })
      .addCase(getProduct.pending, (state) => {
        state.productData = null;
        state.loading = true;
        state.error = null;
      })
      .addCase(getProduct.rejected, (state, action) => {
        state.productData = null;
        state.loading = true;
        state.error = action.error.message;
      });
  },
});
export default productData.reducer;
