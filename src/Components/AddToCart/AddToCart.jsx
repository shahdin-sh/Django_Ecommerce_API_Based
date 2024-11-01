import { useEffect, useState } from "react";
import { useDispatch } from "react-redux";
import { postToCart } from "../../Redux_Toolkit/Cart/AddToCartSlice";

const AddToCart = ({ open, setOpen, productData, quantity, price }) => {
  const [finalCartData, setFinalCartData] = useState({});
  useEffect(() => {
    setFinalCartData((prevData) => ({
      ...prevData,
      current_product_stock: null,
      product: productData,
      quantity: quantity,
      total_price: price,
    }));
  }, [quantity]);
  const dispatch = useDispatch();

  const clickHandler = () => {
    dispatch(postToCart(finalCartData));
    console.log(finalCartData);
    setOpen(!open);
  };

  return (
    <>
      <button onClick={clickHandler} className="px-[42px] bg-[black] flex justify-center items-center text-[white] text-[16px] font-[main]">
        افزودن به سبد خرید
      </button>
    </>
  );
};

export default AddToCart;
