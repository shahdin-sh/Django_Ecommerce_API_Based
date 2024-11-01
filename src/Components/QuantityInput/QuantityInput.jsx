import { useEffect } from "react";

const QuantityInput = ({ inventory, quantity, setQuantity}) => {
  

  const incFunction = () => {
    setQuantity((prevCount) => prevCount + 1);
  };

  const decFunction = () => {
    setQuantity((prevCount) => prevCount - 1);
  };

  return (
    <>
      <div className="py-[10px] px-[15px] border-[1px] flexRow justify-center items-center gap-[15px]">
        <button onClick={decFunction} disabled={quantity === 1} className="text-[14px] text-[rgb(51,51,51)] font-[600]">
          -
        </button>
        <p className="text-[14px] font-[main] text-[rgb(51,51,51)] !w-[50px] text-center focus:outline-none select-none">{quantity}</p>
        <button onClick={incFunction} disabled={quantity === inventory} className="text-[14px] text-[rgb(51,51,51)] font-[600]">
          +
        </button>
      </div>
    </>
  );
};

export default QuantityInput;
