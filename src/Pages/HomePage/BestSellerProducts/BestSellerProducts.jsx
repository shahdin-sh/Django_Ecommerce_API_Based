const BestSellerProducts = () => {
  return (
    <>
      <div className="w-full wrapper flexCol justify-center items-start !mb-[100px]">
        <p className="text-[30px] font-[main] text-[rgb(17,17,17)] mb-[60px]">محصولات پرفروش</p>
        <div className="w-full grid grid-flow-row grid-cols-4 grid-rows-2 gap-[24px]">
          <div className="h-[340px] bg-[rgb(241,241,241)] flex justify-center items-center">Item-1</div>
          <div className="h-[340px] bg-[rgb(241,241,241)] flex justify-center items-center">Item-2</div>
          <div className="h-[340px] bg-[rgb(241,241,241)] flex justify-center items-center">Item-3</div>
          <div className="h-[340px] bg-[rgb(241,241,241)] flex justify-center items-center">Item-4</div>
          <div className="h-[340px] bg-[rgb(241,241,241)] flex justify-center items-center">Item-5</div>
          <div className="h-[340px] bg-[rgb(241,241,241)] flex justify-center items-center">Item-6</div>
          <div className="h-[340px] bg-[rgb(241,241,241)] flex justify-center items-center">Item-7</div>
          <div className="h-[340px] bg-[rgb(241,241,241)] flex justify-center items-center">Item-8</div>
        </div>
      </div>
    </>
  );
};

export default BestSellerProducts;
