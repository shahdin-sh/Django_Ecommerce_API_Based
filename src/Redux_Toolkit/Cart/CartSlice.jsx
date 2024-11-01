import { createAsyncThunk, createSlice } from "@reduxjs/toolkit";
import axios from "axios";

export const getCart = createAsyncThunk("/get/cart", async () => {
  const res = await axios.get("http://0.0.0.0:8000/store/carts/", {
    headers: {
      Authorization: "JWT eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzMwNTM3MTU5LCJpYXQiOjE3MzA0NTA3NTksImp0aSI6IjExZjY5YmJiOTNhZDQzOTFiNjU3YzlmNTgxM2IyODEyIiwidXNlcl9pZCI6ODF9.-tQJYJPPi3-mnRXcVxVCMFID2Cj5VhHiPqHYqDJf7c8",
    },
  });
  return res.data.results;
});

export const cartData = createSlice({
  name: "cart",
  initialState: {
    cartData: null,
    loading: true,
    error: null,
  },
  extraReducers: (Builder) => {
    Builder.addCase(getCart.fulfilled, (state, action) => {
      state.cartData = action.payload;
      state.loading = false;
      state.error = null;
    })
      .addCase(getCart.pending, (state) => {
        state.cartData = null;
        state.loading = true;
        state.error = null;
      })
      .addCase(getCart.rejected, (state, action) => {
        state.cartData = null;
        state.loading = true;
        state.error = action.error.message;
      });
  },
});
export default cartData.reducer;
