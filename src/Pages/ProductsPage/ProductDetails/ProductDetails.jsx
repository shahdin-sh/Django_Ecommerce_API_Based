import { useEffect, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { getProduct } from "../../../Redux_Toolkit/Products/ProductSlice";
import { useParams } from "react-router-dom";
import CategoryLink from "../../../Components/CategoryLink/CategoryLink";
import SubmitHandler from "./SubmitHandler";
import CartSideBar from "../../../Components/CartSideBar/CartSideBar";

const ProductDetails = () => {
  const { productData, loading, error } = useSelector((state) => state.productData);
  const [open, setOpen] = useState(false);
  const [quantity, setQuantity] = useState(1);
  const dispatch = useDispatch();
  const params = useParams();
  const name = params.name;
  const slug = name.replace(/ /g, "-").toLowerCase();

  useEffect(() => {
    dispatch(getProduct(slug));
  }, []);

  if (!productData) {
    return loading ? <p>loading...</p> : "";
  }

  return (
    <>
      <main className="z-[2] bg-[white] !mb-[480px]">
        <div className="w-full py-[80px] bg-[rgb(241,241,241)] flex justify-center items-center text-[30px] font-[main] font-bold mb-[120px]">{productData.name}</div>
        <div className="w-full wrapper flexRow justify-start items-stretch !pb-[120px]">
          <img src={productData.image} alt="" className="max-w-[540px] w-full object-cover" />
          <div className="w-full flexCol justify-start items-start mr-[28px] py-[10px]">
            <p className="text-[24px] font-[main] text-[rgb(17,17,17)] mb-[10px]">{productData.name}</p>
            <p className="text-[30px] text-[rgb(153,153,153)] mb-[20px]">${productData.unit_price}</p>
            <p className="text-[16px] font-[main] text-[rgb(17,17,17)] mb-[20px]">
              موجودی: <span className="text-[rgb(102,102,102)]">{productData.inventory}</span>
            </p>
            <CategoryLink category={productData.category} />
            <SubmitHandler productData={productData} inventory={productData.inventory} open={open} setOpen={setOpen} quantity={quantity} setQuantity={setQuantity} price={productData.unit_price}/>
          </div>
        </div>
      </main>
      {open ? <CartSideBar open={open} setOpen={setOpen} /> : null}
    </>
  );
};

export default ProductDetails;
