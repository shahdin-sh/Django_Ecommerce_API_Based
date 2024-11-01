import { useEffect, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { getCart } from "../../Redux_Toolkit/Cart/CartSlice";
import QuantityHandler from "./QuantityHandler";
import DeleteFromCartSideBar from "./DeleteFromCartSideBar";

const CartSideBar = ({ open, setOpen }) => {
  const { cartData, loading, error } = useSelector((state) => state.cartData);
  const dispatch = useDispatch();
  const [reRender, setReRender] = useState(true);
  const closeHandler = ()=>{
    setOpen(!open)
  }

  useEffect(() => {
    dispatch(getCart());
  }, [reRender]);

  if (!cartData) {
    return loading ? "" : "";
  }

  const myCart = cartData?.[0].items;
  console.log(cartData);

  return (
    <>
      {/* cart items */}
      <div className={`w-[400px] h-[100vh] z-[52] fixed left-0 top-0 bg-white opacity-[1] p-[40px] flexCol justify-start items-start`}>
        {myCart?.map((e) => {
          return (
            <div key={e.id} className="w-full my-[20px] flexRow justify-center items-center">
              <img src="" alt="img" className="w-[50px] h-[50px] ml-[10px]" />
              <p className="text-[12px] font-[main] ml-[10px]">{e.product.name}</p>
              <QuantityHandler realQuantity={e.quantity} />
              <DeleteFromCartSideBar ID={e.id} reRender={reRender} setReRender={setReRender} />
            </div>
          );
        })}
      </div>

      {/* cart background */}
      <div onClick={closeHandler} className={`w-full h-[100vh] z-[51] fixed left-0 top-0 bg-[rgba(0,0,0,0.5)]`}></div>
    </>
  );
};

export default CartSideBar;
