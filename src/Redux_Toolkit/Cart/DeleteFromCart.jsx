import { createAsyncThunk, createSlice } from "@reduxjs/toolkit";
import axios from "axios";

export const DeleteFromCart = createAsyncThunk("/delete/cart", async (ID) => {
  const res = await axios.delete(`http://0.0.0.0:8000/store/carts/e8cbfa36-d806-46f1-a34a-6780cc7ec9b6/items/${ID}`, {
    headers: {
      Authorization: "JWT eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzMwNTM3MTU5LCJpYXQiOjE3MzA0NTA3NTksImp0aSI6IjExZjY5YmJiOTNhZDQzOTFiNjU3YzlmNTgxM2IyODEyIiwidXNlcl9pZCI6ODF9.-tQJYJPPi3-mnRXcVxVCMFID2Cj5VhHiPqHYqDJf7c8",
    },
  });
  return res.data;
});

export const deletedFromCart = createSlice({
  name: "deleteFromCart",
  initialState: {
    deleteFromCart: null,
    loading: true,
    error: null,
  },
  extraReducers: (Builder) => {
    Builder.addCase(DeleteFromCart.fulfilled, (state, action) => {
      state.deleteFromCart = action.payload;
      state.loading = false;
      state.error = null;
    })
      .addCase(DeleteFromCart.pending, (state) => {
        state.deleteFromCart = null;
        state.loading = true;
        state.error = null;
      })
      .addCase(DeleteFromCart.rejected, (state, action) => {
        state.deleteFromCart = null;
        state.loading = true;
        state.error = action.error.message;
      });
  },
});
export default deletedFromCart.reducer;
