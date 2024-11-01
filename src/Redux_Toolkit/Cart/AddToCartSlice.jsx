import { createAsyncThunk, createSlice } from "@reduxjs/toolkit";
import axios from "axios";

export const postToCart = createAsyncThunk("/post/cart", async (data) => {
  const res = await axios.post("http://0.0.0.0:8000/store/carts/e8cbfa36-d806-46f1-a34a-6780cc7ec9b6/items/", data, {
    headers: {
      Authorization: "JWT eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzMwNTM3MTU5LCJpYXQiOjE3MzA0NTA3NTksImp0aSI6IjExZjY5YmJiOTNhZDQzOTFiNjU3YzlmNTgxM2IyODEyIiwidXNlcl9pZCI6ODF9.-tQJYJPPi3-mnRXcVxVCMFID2Cj5VhHiPqHYqDJf7c8",
    },
  });
  return res.data;
});

export const postedToCart = createSlice({
  name: "postedToCart",
  initialState: {
    postedToCart: null,
    loading: true,
    error: null,
  },
  extraReducers: (Builder) => {
    Builder.addCase(postToCart.fulfilled, (state, action) => {
      state.postedToCart = action.payload;
      state.loading = false;
      state.error = null;
    })
      .addCase(postToCart.pending, (state) => {
        state.postedToCart = null;
        state.loading = true;
        state.error = null;
      })
      .addCase(postToCart.rejected, (state, action) => {
        state.postedToCart = null;
        state.loading = true;
        state.error = action.error.message;
      });
  },
});
export default postedToCart.reducer;
