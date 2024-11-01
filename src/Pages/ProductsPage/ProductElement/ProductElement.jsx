import { Link } from "react-router-dom";

const ProductElement = ({ name, img, price }) => {
  return (
    <>
     <Link to={`/products/${name}`}>
     <div className="flexCol justify-center items-center">
        <img src={img} alt="" className="w-full object-fill" />
        <div className="w-full p-[20px] flexCol justify-center items-center">
          <p className="text-[16px] text-[rgb(17,17,17)] mb-[10px]">{name}</p>
          <p className="text-[14px] text-[rgb(102,102,102)]">${price}</p>
        </div>
      </div>
     </Link>
    </>
  );
};

export default ProductElement;
