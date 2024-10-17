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

  console.log(productsData);

  return <>
  <div className="w-full wrapper grid grid-flow-row grid-cols-5 gap-[15px]">
  {productsData?.map((element, index)=>{
    return <ProductElement name={element.name} key={index} img={element.image}/>
  })}  
  </div>
  </>;
};

export default ProductsPage;
