import { useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import { getCart } from "../../Redux_Toolkit/Cart/CartSlice";
import QuantityFunction from "./QuantiityFunction";

const CartPage = () => {
  const { cartData, loading, error } = useSelector((state) => state.cartData);
  const dispatch = useDispatch();

  useEffect(() => {
    dispatch(getCart());
  }, []);

  if (!cartData) {
    return loading ? "" : "";
  }

  const myCart = cartData?.[0].items;
  console.log(myCart);

  return (
    <>
      <div className="w-full bg-white z-[2]">
        <div className="w-full bg-[rgb(241,241,241)] !py-[80px]">
          <div className="wrapper  w-full flex justify-center items-center">
            <h1 className="text-[rgb(17,17,17)] text-[36px] font-[main]">سبد خرید</h1>
          </div>
        </div>
        <div className="wrapper w-full !py-[90px] !mb-[480px] flexCol justify-center items-center">
          <div className="w-full flexRow justify-center items-stretch p-[20px] bg-[rgb(241,241,241)] text-[18px] font-[main]">
            <span className="w-[30%]">محصول</span>
            <span className="w-[25%]">قیمت</span>
            <span className="w-[25%]">تعداد</span>
            <span className="w-[15%]">جمع</span>
            <div className="w-[5%]"></div>
          </div>
          {myCart?.map((e) => {
            return (
              <div key={e.id} className="w-full flexRow justify-center items-stretch p-[20px] text-[18px] font-[main] py-[10px] border-b-[1px] border-b-[rgb(241,241,241)]">
                <div className="w-[30%] flexRow justify-start items-center gap-[10px]">
                  <img src="" alt="img" className="w-[70px] h-[70px]" />
                  <p className="text-[16px] font-[main]">{e.product.name}</p>
                </div>

                <div className="w-[25%] flex justify-start items-center text-[16px] font-[main]">
                  <p className="flex justify-center items-center">{e.product.unit_price}</p>
                </div>

                <div className="w-[25%] flex justify-start items-center">
                  <QuantityFunction realQuantity={e.quantity} />
                </div>
                <div className="w-[15%] flex justify-start items-center">
                  <span className="text-[12px] font-[main]">{parseFloat()}</span>
                </div>
                <div className="w-[5%]"></div>
              </div>
            );
          })}
        </div>
      </div>
    </>
  );
};

export default CartPage;
