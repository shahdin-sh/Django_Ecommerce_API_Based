import { useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import { fetchProducts } from "../../Redux_Toolkit/Products/ProductsSlice";
import ProductElement from "./ProductElement/ProductElement";

const ProductsPage = () => {
  const { productsData, loading, error } = useSelector((state) => state.productsData);
  const dispatch = useDispatch();

  useEffect(() => {
    dispatch(fetchProducts());
  }, []);


  return (
    <>
      <main className="z-[2] bg-white mb-[480px]">
        <div className="w-full py-[80px] bg-[rgb(241,241,241)] flex justify-center items-center text-[30px] font-[main] font-bold mb-[120px]">فروشگاه</div>
        <div className="w-full wrapper grid grid-flow-row grid-cols-4 gap-[25px] !pb-[120px]">
          {productsData?.map((element, index) => {
            return <ProductElement name={element.name} key={index} img={element.image} price={element.unit_price} />;
          })}
        </div>
      </main>
    </>
  );
};

export default ProductsPage;
