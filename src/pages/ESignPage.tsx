import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { CheckCircle, FileText } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Checkbox } from "@/components/ui/checkbox";

const ESignPage = () => {
  const [name, setName] = useState("");
  const [agreed, setAgreed] = useState(false);
  const [signed, setSigned] = useState(false);

  const handleSign = () => {
    if (name && agreed) setSigned(true);
  };

  return (
    <div className="min-h-screen bg-[hsl(0,0%,98%)] text-[hsl(222,84%,4.9%)] flex items-center justify-center p-6">
      <motion.div
        className="w-full max-w-2xl bg-white rounded-2xl shadow-2xl border border-gray-100 overflow-hidden"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <AnimatePresence mode="wait">
          {!signed ? (
            <motion.div key="form" exit={{ opacity: 0, scale: 0.95 }} className="p-8 space-y-6">
              <div className="flex items-center gap-3 mb-2">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center text-white font-bold">
                  Q
                </div>
                <div>
                  <h1 className="text-2xl font-bold text-gray-900">Sign Contract</h1>
                  <p className="text-sm text-gray-500">QTC Construction Management</p>
                </div>
              </div>

              {/* Contract Content */}
              <div className="max-h-72 overflow-auto rounded-xl bg-gray-50 border border-gray-200 p-6">
                <div className="flex items-center gap-2 mb-4">
                  <FileText className="h-5 w-5 text-gray-400" />
                  <h2 className="font-semibold text-gray-700">Construction Agreement</h2>
                </div>
                <div className="text-sm text-gray-600 space-y-3 leading-relaxed">
                  <p>This agreement is entered into between QTC Construction LLC and the signee for the completion of construction work as outlined in the project scope.</p>
                  <p><strong>Scope of Work:</strong> As described in the attached project documentation.</p>
                  <p><strong>Payment Terms:</strong> Milestone-based payments as outlined in the invoice schedule.</p>
                  <p><strong>Timeline:</strong> Work to be completed within the agreed-upon timeframe from the contract start date.</p>
                  <p>Both parties agree to the terms and conditions outlined in this contract and any attached addenda.</p>
                </div>
              </div>

              {/* Sign Fields */}
              <div className="space-y-4">
                <div>
                  <label className="text-sm font-medium text-gray-700 mb-1.5 block">Full Name</label>
                  <Input
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="Enter your full name"
                    className="border-gray-300 bg-white text-gray-900 placeholder:text-gray-400 focus:border-blue-500 focus:ring-blue-500"
                  />
                </div>
                <label className="flex items-center gap-3 cursor-pointer">
                  <Checkbox
                    checked={agreed}
                    onCheckedChange={(v) => setAgreed(v as boolean)}
                    className="border-gray-300 data-[state=checked]:bg-blue-500 data-[state=checked]:border-blue-500"
                  />
                  <span className="text-sm text-gray-600">I agree to sign this contract electronically</span>
                </label>
              </div>

              <Button
                className="w-full py-6 text-base font-semibold rounded-xl bg-gradient-to-r from-blue-500 to-purple-500 text-white hover:brightness-110 transition-all disabled:opacity-40"
                disabled={!name || !agreed}
                onClick={handleSign}
              >
                Sign Contract
              </Button>
            </motion.div>
          ) : (
            <motion.div
              key="success"
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              className="p-12 text-center space-y-4"
            >
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ type: "spring", delay: 0.2 }}
              >
                <CheckCircle className="h-20 w-20 text-green-500 mx-auto" style={{ filter: "drop-shadow(0 0 16px rgba(34,197,94,0.4))" }} />
              </motion.div>
              <h2 className="text-2xl font-bold text-gray-900">Contract Signed!</h2>
              <p className="text-gray-500">Thank you, {name}. A copy will be emailed to you shortly.</p>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>
    </div>
  );
};

export default ESignPage;
