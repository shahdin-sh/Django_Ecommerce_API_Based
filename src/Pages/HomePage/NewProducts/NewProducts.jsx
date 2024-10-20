import NewProductsSlider from "./NewProductsSlider";

const NewProducts = () => {
  return (
    <>
      <div className="w-full wrapper flexCol justify-center items-start !mb-[120px]">
        <p className="text-[30px] font-[main] text-[rgb(17,17,17)] mb-[60px]">محصولات جدید</p>
        <NewProductsSlider/>
      </div>
    </>
  );
};

export default NewProducts;
