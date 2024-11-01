import { useState } from "react";

const QuantityFunction = ({ realQuantity }) => {
  const [quantity, setQuantity] = useState(realQuantity);

  const inc = () => {
    setQuantity(quantity + 1);
  };

  const dec = () => {
    setQuantity(quantity - 1);
  };

  return (
    <>
      <div className="w-[100px] flexRow justify-center items-center">
        <button onClick={inc} className="w-full flex justify-center items-center">
          +
        </button>
        <span className="w-full flex justify-center items-center text-[12px] font-[main]">{quantity}</span>
        <button onClick={dec} className="w-full flex justify-center items-center">
          -
        </button>
      </div>
    </>
  );
};

export default QuantityFunction;
