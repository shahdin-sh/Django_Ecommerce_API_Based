import { configureStore } from "@reduxjs/toolkit";
import ProductsReducer from "./Products/ProductsSlice";
import ProductReducer from "./Products/ProductSlice";
import CategoryReducer from "./Categoties/CategorySlice";
import CartReducer from "./Cart/CartSlice";
import DeleteFromCartReducer from "./Cart/DeleteFromCart";
import AddToCartReducer from "./Cart/AddToCartSlice";

export const store = configureStore({
  reducer: {
    productsData: ProductsReducer,
    productData: ProductReducer,
    categoryData: CategoryReducer,
    cartData: CartReducer,
    deletedFromCart: DeleteFromCartReducer,
    postedToCart: AddToCartReducer,
  },
});
