const ProductElement = ({name,img}) => {
  return ( <>
  <div className="flexCol justify-center items-center bg-green-500 p-[20px]">
    <img src={img} alt=""  className="w-full object-fill mb-[20px]"/>
    <p>{name}</p>
  </div>
  </> );
}
 
export default ProductElement;