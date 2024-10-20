import classes from "./styles.module.css"

const Footer = () => {
  return ( <>
  <footer className={`w-full h-[480px] flex justify-center items-center text-[30px] bg-[rgb(241,241,241)] ${classes.footer} ${classes.reveal} z-[-1]`}>
    FOOTER
  </footer>
  </> );
}
 
export default Footer;