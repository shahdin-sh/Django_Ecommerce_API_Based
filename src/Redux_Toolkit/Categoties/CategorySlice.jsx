import { createAsyncThunk, createSlice } from "@reduxjs/toolkit";
import axios from "axios";

export const getCategory = createAsyncThunk("/get/category", async (category) => {
  const res = await axios.get(`${category}`);
  return res.data;
});

export const categoryData = createSlice({
  name: "category",
  initialState: {
    categoryData: null,
    loading: true,
    error: null,
  },
  extraReducers: (Builder) => {
    Builder.addCase(getCategory.fulfilled, (state, action) => {
      state.categoryData = action.payload;
      state.loading = false;
      state.error = null;
    })
      .addCase(getCategory.pending, (state) => {
        state.categoryData = null;
        state.loading = true;
        state.error = null;
      })
      .addCase(getCategory.rejected, (state, action) => {
        state.categoryData = null;
        state.loading = true;
        state.error = action.error.message;
      });
  },
});
export default categoryData.reducer